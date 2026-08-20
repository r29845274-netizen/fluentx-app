-- Secure admin authorization + audit logging. Client access is denied; only
-- trusted backend code using the Supabase service/secret role may read/write.
create table if not exists public.admin_users (
  user_id uuid primary key references auth.users(id) on delete cascade,
  role text not null default 'admin' check (role in ('owner','admin','support')),
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  created_by uuid references auth.users(id) on delete set null
);

create table if not exists public.admin_audit_log (
  id bigint generated always as identity primary key,
  admin_user_id uuid not null references auth.users(id) on delete restrict,
  action text not null,
  target_user_id uuid references auth.users(id) on delete set null,
  reason text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists admin_audit_admin_created_idx on public.admin_audit_log(admin_user_id, created_at desc);
create index if not exists admin_audit_target_created_idx on public.admin_audit_log(target_user_id, created_at desc);

alter table public.admin_users enable row level security;
alter table public.admin_audit_log enable row level security;

revoke all on table public.admin_users from public, anon, authenticated;
revoke all on table public.admin_audit_log from public, anon, authenticated;
revoke all on sequence public.admin_audit_log_id_seq from public, anon, authenticated;
grant select, insert, update, delete on table public.admin_users to service_role;
grant select, insert, update, delete on table public.admin_audit_log to service_role;
grant usage, select on sequence public.admin_audit_log_id_seq to service_role;

drop policy if exists "Deny client access to admin users" on public.admin_users;
create policy "Deny client access to admin users" on public.admin_users as restrictive for all to anon, authenticated using(false) with check(false);
drop policy if exists "Deny client access to admin audit log" on public.admin_audit_log;
create policy "Deny client access to admin audit log" on public.admin_audit_log as restrictive for all to anon, authenticated using(false) with check(false);

revoke all on table
  public.user_home_stats, public.vocabulary_words, public.user_vocabulary_progress,
  public.grammar_lessons, public.grammar_questions, public.user_grammar_mistakes,
  public.listening_clips, public.listening_questions, public.user_listening_progress,
  public.writing_prompts, public.writing_submissions, public.ai_practice_scenarios,
  public.ai_practice_sessions
from anon;

-- Users need scenario metadata, never the private AI system prompt.
revoke select on table public.ai_practice_scenarios from authenticated;
grant select(id, title, category, description, created_at) on table public.ai_practice_scenarios to authenticated;
grant select on table public.ai_practice_scenarios to service_role;

-- Deny-by-default for future public objects.
alter default privileges for role postgres in schema public revoke select, insert, update, delete on tables from anon, authenticated;
alter default privileges for role postgres in schema public revoke usage, select on sequences from anon, authenticated;
alter default privileges for role postgres in schema public revoke execute on functions from anon, authenticated, public;

create schema if not exists private;
revoke all on schema private from public, anon, authenticated;

create or replace function private.rls_auto_enable()
returns event_trigger
language plpgsql
security definer
set search_path = pg_catalog
as $$
declare cmd record;
begin
  for cmd in select * from pg_event_trigger_ddl_commands()
    where command_tag in ('CREATE TABLE','CREATE TABLE AS','SELECT INTO')
      and object_type in ('table','partitioned table')
  loop
    if cmd.schema_name = 'public' then
      begin
        execute format('alter table if exists %s enable row level security', cmd.object_identity);
      exception when others then
        raise log 'rls_auto_enable failed for %: %', cmd.object_identity, sqlerrm;
      end;
    end if;
  end loop;
end;
$$;
revoke all on function private.rls_auto_enable() from public, anon, authenticated;
drop event trigger if exists fluentx_ensure_rls;
create event trigger fluentx_ensure_rls on ddl_command_end
when tag in ('CREATE TABLE','CREATE TABLE AS','SELECT INTO')
execute function private.rls_auto_enable();
