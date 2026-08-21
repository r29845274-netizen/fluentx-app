-- FluentX runtime progression + server-side subscription access hardening.
-- Mirrors the production Supabase migration applied on 2026-08-21.

create table if not exists public.user_week_component_progress (
  user_id uuid not null references auth.users(id) on delete cascade,
  week_id uuid not null references public.learning_weeks(id) on delete cascade,
  component_id uuid not null references public.learning_week_components(id) on delete cascade,
  completed_count integer not null default 0 check (completed_count >= 0),
  status text not null default 'not_started' check (status in ('not_started','in_progress','completed')),
  first_started_at timestamptz,
  last_completed_at timestamptz,
  updated_at timestamptz not null default now(),
  primary key (user_id, component_id)
);
create index if not exists user_week_component_progress_user_week_idx on public.user_week_component_progress(user_id, week_id);
alter table public.user_week_component_progress enable row level security;
drop policy if exists "Users read own week component progress" on public.user_week_component_progress;
create policy "Users read own week component progress" on public.user_week_component_progress for select to authenticated using ((select auth.uid()) = user_id);
revoke insert, update, delete on public.user_week_component_progress from anon, authenticated;
grant select on public.user_week_component_progress to authenticated;

create table if not exists public.weekly_mastery_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  week_id uuid not null references public.learning_weeks(id) on delete cascade,
  questions jsonb not null,
  status text not null default 'started' check (status in ('started','submitted','expired')),
  created_at timestamptz not null default now(),
  submitted_at timestamptz
);
create index if not exists weekly_mastery_sessions_user_week_created_idx on public.weekly_mastery_sessions(user_id, week_id, created_at desc);
alter table public.weekly_mastery_sessions enable row level security;
revoke all on public.weekly_mastery_sessions from anon, authenticated;

create table if not exists public.user_subscription_access (
  user_id uuid primary key references auth.users(id) on delete cascade,
  tier text not null default 'free' check (tier in ('free','monthly','annual')),
  entitlement_active boolean not null default false,
  product_identifier text,
  expires_at timestamptz,
  verified_at timestamptz not null default now(),
  source text not null default 'revenuecat',
  updated_at timestamptz not null default now()
);
alter table public.user_subscription_access enable row level security;
drop policy if exists "Users read own verified subscription access" on public.user_subscription_access;
create policy "Users read own verified subscription access" on public.user_subscription_access for select to authenticated using ((select auth.uid()) = user_id);
revoke insert, update, delete on public.user_subscription_access from anon, authenticated;
grant select on public.user_subscription_access to authenticated;

create index if not exists ai_practice_sessions_user_started_idx on public.ai_practice_sessions(user_id, started_at desc);
create index if not exists writing_submissions_user_scored_idx on public.writing_submissions(user_id, scored_at desc);
create index if not exists weekly_test_attempts_user_week_created_idx on public.weekly_test_attempts(user_id, week_id, created_at desc);

-- Runtime RPCs are created/updated by the production migration and intentionally
-- use auth.uid() ownership checks. Edge Functions hold mastery answer keys and
-- subscription-verification authority; clients cannot mutate those tables.
