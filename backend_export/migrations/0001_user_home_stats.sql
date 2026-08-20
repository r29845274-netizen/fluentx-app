-- FluentX — user_home_stats
-- Backs the Home screen's daily goal, streak, XP, and "continue
-- learning" prompt. One row per user, created lazily on first Home
-- screen load (see HomeRemoteDataSourceImpl.getHomeSummary).

create table if not exists public.user_home_stats (
  user_id uuid primary key references auth.users (id) on delete cascade,
  streak_days integer not null default 0,
  xp_earned integer not null default 0,
  daily_goal_target_minutes integer not null default 10,
  daily_goal_progress_minutes integer not null default 0,
  continue_title text,
  continue_level_label text,
  continue_progress_percent numeric(5, 2) not null default 0,
  updated_at timestamptz not null default now()
);

-- Keep updated_at current on every write.
create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_user_home_stats_updated_at on public.user_home_stats;
create trigger trg_user_home_stats_updated_at
  before update on public.user_home_stats
  for each row execute function public.set_updated_at();

-- Row Level Security: a user can only ever see/modify their own row.
alter table public.user_home_stats enable row level security;

drop policy if exists "Users can view own home stats" on public.user_home_stats;
create policy "Users can view own home stats"
  on public.user_home_stats for select
  using (auth.uid() = user_id);

drop policy if exists "Users can insert own home stats" on public.user_home_stats;
create policy "Users can insert own home stats"
  on public.user_home_stats for insert
  with check (auth.uid() = user_id);

drop policy if exists "Users can update own home stats" on public.user_home_stats;
create policy "Users can update own home stats"
  on public.user_home_stats for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
