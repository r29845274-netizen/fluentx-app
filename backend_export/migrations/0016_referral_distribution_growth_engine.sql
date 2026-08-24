-- FluentX referral + distribution growth engine.
-- Mirrors production migration referral_distribution_growth_engine.

create table if not exists public.user_referral_codes (
  user_id uuid primary key references auth.users(id) on delete cascade,
  code text not null unique,
  created_at timestamptz not null default now()
);

create table if not exists public.referral_redemptions (
  referred_user_id uuid primary key references auth.users(id) on delete cascade,
  referrer_user_id uuid not null references auth.users(id) on delete cascade,
  referral_code text not null,
  referrer_xp_awarded integer not null default 100,
  referred_xp_awarded integer not null default 50,
  created_at timestamptz not null default now(),
  check (referred_user_id <> referrer_user_id)
);

create index if not exists referral_redemptions_referrer_idx
  on public.referral_redemptions(referrer_user_id, created_at desc);

create table if not exists public.growth_events (
  id bigserial primary key,
  user_id uuid references auth.users(id) on delete set null,
  event_name text not null,
  source text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists growth_events_user_idx on public.growth_events(user_id, created_at desc);
create index if not exists growth_events_event_idx on public.growth_events(event_name, created_at desc);

alter table public.user_referral_codes enable row level security;
alter table public.referral_redemptions enable row level security;
alter table public.growth_events enable row level security;

drop policy if exists "Users read own referral code" on public.user_referral_codes;
create policy "Users read own referral code" on public.user_referral_codes
  for select to authenticated using ((select auth.uid()) = user_id);

drop policy if exists "Users read own referral results" on public.referral_redemptions;
create policy "Users read own referral results" on public.referral_redemptions
  for select to authenticated
  using ((select auth.uid()) = referred_user_id or (select auth.uid()) = referrer_user_id);

revoke insert, update, delete on public.user_referral_codes from anon, authenticated;
revoke insert, update, delete on public.referral_redemptions from anon, authenticated;
revoke all on public.growth_events from anon, authenticated;
grant select on public.user_referral_codes to authenticated;
grant select on public.referral_redemptions to authenticated;

create or replace function public.get_my_referral_dashboard() returns jsonb
language plpgsql security definer set search_path to 'public','pg_temp'
as $$
declare v_uid uuid := auth.uid(); v_code text; v_count integer; v_xp integer;
begin
  if v_uid is null then raise exception 'Authentication required' using errcode='42501'; end if;
  insert into public.user_referral_codes(user_id, code)
  values (v_uid, 'FX' || upper(substr(replace(v_uid::text, '-', ''), 1, 10)))
  on conflict (user_id) do nothing;
  select code into v_code from public.user_referral_codes where user_id = v_uid;
  select count(*), coalesce(sum(referrer_xp_awarded),0) into v_count, v_xp
  from public.referral_redemptions where referrer_user_id = v_uid;
  return jsonb_build_object('code',v_code,'successful_referrals',v_count,'earned_xp',v_xp,'reward_referrer_xp',100,'reward_friend_xp',50);
end;
$$;
grant execute on function public.get_my_referral_dashboard() to authenticated;

create or replace function public.track_growth_event(p_event_name text, p_source text default null, p_metadata jsonb default '{}'::jsonb)
returns void language plpgsql security definer set search_path to 'public','pg_temp'
as $$
declare v_uid uuid := auth.uid(); v_event text := lower(trim(coalesce(p_event_name,''))); v_source text := left(nullif(trim(coalesce(p_source,'')),''),64);
begin
  if v_uid is null then raise exception 'Authentication required' using errcode='42501'; end if;
  if v_event = '' or length(v_event) > 64 then raise exception 'Invalid event name' using errcode='22023'; end if;
  insert into public.growth_events(user_id,event_name,source,metadata) values(v_uid,v_event,v_source,coalesce(p_metadata,'{}'::jsonb));
end;
$$;
grant execute on function public.track_growth_event(text,text,jsonb) to authenticated;

create or replace function public.redeem_referral_code(p_code text) returns jsonb
language plpgsql security definer set search_path to 'public','pg_temp'
as $$
declare v_uid uuid := auth.uid(); v_code text := upper(trim(coalesce(p_code,''))); v_referrer uuid; v_existing uuid;
begin
  if v_uid is null then raise exception 'Authentication required' using errcode='42501'; end if;
  if v_code = '' then raise exception 'Referral code is required' using errcode='22023'; end if;
  select referred_user_id into v_existing from public.referral_redemptions where referred_user_id=v_uid;
  if v_existing is not null then return jsonb_build_object('success',false,'already_redeemed',true,'message','You have already used a referral code.'); end if;
  select user_id into v_referrer from public.user_referral_codes where code=v_code;
  if v_referrer is null then raise exception 'Referral code not found' using errcode='P0002'; end if;
  if v_referrer=v_uid then raise exception 'You cannot use your own referral code' using errcode='22023'; end if;
  insert into public.referral_redemptions(referred_user_id,referrer_user_id,referral_code)
  values(v_uid,v_referrer,v_code) on conflict(referred_user_id) do nothing;
  insert into public.user_home_stats(user_id,xp_earned) values(v_referrer,100)
  on conflict(user_id) do update set xp_earned=greatest(0,coalesce(public.user_home_stats.xp_earned,0))+100, updated_at=now();
  insert into public.user_home_stats(user_id,xp_earned) values(v_uid,50)
  on conflict(user_id) do update set xp_earned=greatest(0,coalesce(public.user_home_stats.xp_earned,0))+50, updated_at=now();
  insert into public.growth_events(user_id,event_name,source,metadata) values
    (v_uid,'referral_redeemed','referral_screen',jsonb_build_object('code',v_code)),
    (v_referrer,'referral_success','referral_program',jsonb_build_object('referred_user_id',v_uid));
  return jsonb_build_object('success',true,'friend_xp_awarded',50,'referrer_xp_awarded',100,'message','Referral applied. You earned 50 XP.');
end;
$$;
grant execute on function public.redeem_referral_code(text) to authenticated;
