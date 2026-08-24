-- FluentX legal compliance completion.
-- Mirrors production migration legal_compliance_completion.

create table if not exists public.user_legal_acceptances (
  user_id uuid primary key references auth.users(id) on delete cascade,
  terms_version text not null,
  privacy_version text not null,
  accepted_at timestamptz not null default now(),
  acceptance_source text not null default 'onboarding',
  updated_at timestamptz not null default now()
);
alter table public.user_legal_acceptances enable row level security;
drop policy if exists "Users read own legal acceptance" on public.user_legal_acceptances;
create policy "Users read own legal acceptance" on public.user_legal_acceptances for select to authenticated using ((select auth.uid())=user_id);
revoke insert,update,delete on public.user_legal_acceptances from anon,authenticated;
grant select on public.user_legal_acceptances to authenticated;

create table if not exists public.legal_requests (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  request_type text not null check(request_type in('ip_infringement','privacy_access','privacy_correction','privacy_deletion','data_question','other_legal')),
  claimant_name text not null,
  contact_email text not null,
  subject text not null,
  details text not null,
  original_work text,
  material_location text,
  authority_confirmed boolean not null default false,
  accuracy_confirmed boolean not null default false,
  status text not null default 'received' check(status in('received','under_review','actioned','closed','rejected')),
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create index if not exists legal_requests_user_created_idx on public.legal_requests(user_id,created_at desc);
create index if not exists legal_requests_status_created_idx on public.legal_requests(status,created_at desc);
alter table public.legal_requests enable row level security;
drop policy if exists "Users read own legal requests" on public.legal_requests;
create policy "Users read own legal requests" on public.legal_requests for select to authenticated using ((select auth.uid())=user_id);
revoke insert,update,delete on public.legal_requests from anon,authenticated;
grant select on public.legal_requests to authenticated;

create or replace function public.accept_current_legal_documents(p_source text default 'onboarding') returns jsonb
language plpgsql security definer set search_path to 'public','pg_temp'
as $$
declare v_uid uuid:=auth.uid(); v_terms constant text:='2026-08-24'; v_privacy constant text:='2026-08-24'; v_source text:=left(coalesce(nullif(trim(p_source),''),'onboarding'),64);
begin
 if v_uid is null then raise exception 'Authentication required' using errcode='42501'; end if;
 insert into public.user_legal_acceptances(user_id,terms_version,privacy_version,accepted_at,acceptance_source,updated_at)
 values(v_uid,v_terms,v_privacy,now(),v_source,now()) on conflict(user_id) do update set terms_version=excluded.terms_version,privacy_version=excluded.privacy_version,accepted_at=excluded.accepted_at,acceptance_source=excluded.acceptance_source,updated_at=excluded.updated_at;
 return jsonb_build_object('accepted',true,'terms_version',v_terms,'privacy_version',v_privacy,'accepted_at',now());
end;$$;
grant execute on function public.accept_current_legal_documents(text) to authenticated;

create or replace function public.get_my_legal_status() returns jsonb
language plpgsql stable security definer set search_path to 'public','pg_temp'
as $$
declare v_uid uuid:=auth.uid(); v_terms constant text:='2026-08-24'; v_privacy constant text:='2026-08-24'; v_row public.user_legal_acceptances%rowtype; v_open integer;
begin
 if v_uid is null then raise exception 'Authentication required' using errcode='42501'; end if;
 select * into v_row from public.user_legal_acceptances where user_id=v_uid;
 select count(*) into v_open from public.legal_requests where user_id=v_uid and status in('received','under_review');
 return jsonb_build_object('accepted_current',v_row.user_id is not null and v_row.terms_version=v_terms and v_row.privacy_version=v_privacy,'terms_version',v_terms,'privacy_version',v_privacy,'accepted_at',v_row.accepted_at,'open_requests',v_open);
end;$$;
grant execute on function public.get_my_legal_status() to authenticated;

create or replace function public.submit_legal_request(p_request_type text,p_claimant_name text,p_contact_email text,p_subject text,p_details text,p_original_work text default null,p_material_location text default null,p_authority_confirmed boolean default false,p_accuracy_confirmed boolean default false) returns jsonb
language plpgsql security definer set search_path to 'public','pg_temp'
as $$
declare v_uid uuid:=auth.uid(); v_type text:=lower(trim(coalesce(p_request_type,''))); v_name text:=trim(coalesce(p_claimant_name,'')); v_email text:=lower(trim(coalesce(p_contact_email,''))); v_subject text:=trim(coalesce(p_subject,'')); v_details text:=trim(coalesce(p_details,'')); v_id uuid;
begin
 if v_uid is null then raise exception 'Authentication required' using errcode='42501'; end if;
 if v_type not in('ip_infringement','privacy_access','privacy_correction','privacy_deletion','data_question','other_legal') then raise exception 'Invalid request type' using errcode='22023'; end if;
 if length(v_name)<2 or length(v_name)>120 then raise exception 'Valid claimant name is required' using errcode='22023'; end if;
 if length(v_email)<5 or length(v_email)>200 or position('@' in v_email)=0 then raise exception 'Valid contact email is required' using errcode='22023'; end if;
 if length(v_subject)<3 or length(v_subject)>180 then raise exception 'Subject must be between 3 and 180 characters' using errcode='22023'; end if;
 if length(v_details)<20 or length(v_details)>8000 then raise exception 'Details must be between 20 and 8000 characters' using errcode='22023'; end if;
 if not coalesce(p_accuracy_confirmed,false) then raise exception 'Accuracy confirmation is required' using errcode='22023'; end if;
 if v_type='ip_infringement' then
  if length(trim(coalesce(p_original_work,'')))<5 then raise exception 'Describe the original protected work' using errcode='22023'; end if;
  if length(trim(coalesce(p_material_location,'')))<5 then raise exception 'Identify the allegedly infringing material and its location' using errcode='22023'; end if;
  if not coalesce(p_authority_confirmed,false) then raise exception 'Authority confirmation is required for IP reports' using errcode='22023'; end if;
 end if;
 insert into public.legal_requests(user_id,request_type,claimant_name,contact_email,subject,details,original_work,material_location,authority_confirmed,accuracy_confirmed,status,created_at,updated_at)
 values(v_uid,v_type,left(v_name,120),left(v_email,200),left(v_subject,180),left(v_details,8000),nullif(left(trim(coalesce(p_original_work,'')),3000),''),nullif(left(trim(coalesce(p_material_location,'')),3000),''),coalesce(p_authority_confirmed,false),coalesce(p_accuracy_confirmed,false),'received',now(),now()) returning id into v_id;
 return jsonb_build_object('success',true,'request_id',v_id,'status','received');
end;$$;
grant execute on function public.submit_legal_request(text,text,text,text,text,text,text,boolean,boolean) to authenticated;
