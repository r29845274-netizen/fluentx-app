-- FluentX growth/retention activity engine.
-- Mirrors production migration growth_retention_activity_engine.

alter table public.user_home_stats
  add column if not exists last_activity_date date,
  add column if not exists daily_goal_progress_date date,
  add column if not exists total_active_days integer not null default 0,
  add column if not exists last_activity_source text;

create table if not exists public.user_daily_activity (
  user_id uuid not null references auth.users(id) on delete cascade,
  activity_date date not null,
  minutes integer not null default 0 check (minutes >= 0),
  xp integer not null default 0 check (xp >= 0),
  events integer not null default 0 check (events >= 0),
  last_source text,
  updated_at timestamptz not null default now(),
  primary key (user_id, activity_date)
);

alter table public.user_daily_activity enable row level security;
drop policy if exists "Users read own daily activity" on public.user_daily_activity;
create policy "Users read own daily activity" on public.user_daily_activity
  for select to authenticated using ((select auth.uid()) = user_id);
revoke insert, update, delete on public.user_daily_activity from anon, authenticated;
grant select on public.user_daily_activity to authenticated;

create or replace function public.record_my_learning_activity(
  p_minutes integer default 1,
  p_xp integer default 5,
  p_source text default 'learning'
) returns jsonb
language plpgsql
security definer
set search_path to 'public','pg_temp'
as $$
declare
  v_uid uuid := auth.uid();
  v_today date := (timezone('Asia/Kolkata', now()))::date;
  v_yesterday date := ((timezone('Asia/Kolkata', now()))::date - 1);
  v_last date;
  v_streak integer;
  v_daily integer;
  v_total_days integer;
  v_minutes integer := greatest(0, least(coalesce(p_minutes, 0), 180));
  v_xp integer := greatest(0, least(coalesce(p_xp, 0), 500));
  v_source text := left(coalesce(nullif(trim(p_source),''), 'learning'), 64);
begin
  if v_uid is null then raise exception 'Authentication required' using errcode='42501'; end if;

  insert into public.user_home_stats(user_id) values (v_uid) on conflict (user_id) do nothing;
  select last_activity_date, streak_days, total_active_days
    into v_last, v_streak, v_total_days
  from public.user_home_stats where user_id = v_uid for update;

  if v_last is null then
    v_streak := 1; v_total_days := greatest(coalesce(v_total_days,0),0) + 1;
  elsif v_last = v_today then
    v_streak := greatest(coalesce(v_streak,0),1);
  elsif v_last = v_yesterday then
    v_streak := greatest(coalesce(v_streak,0),0) + 1;
    v_total_days := greatest(coalesce(v_total_days,0),0) + 1;
  else
    v_streak := 1; v_total_days := greatest(coalesce(v_total_days,0),0) + 1;
  end if;

  update public.user_home_stats
  set streak_days = v_streak,
      xp_earned = greatest(0, coalesce(xp_earned,0)) + v_xp,
      daily_goal_progress_minutes = case
        when daily_goal_progress_date = v_today then greatest(0, coalesce(daily_goal_progress_minutes,0)) + v_minutes
        else v_minutes end,
      daily_goal_progress_date = v_today,
      last_activity_date = v_today,
      total_active_days = v_total_days,
      last_activity_source = v_source,
      updated_at = now()
  where user_id = v_uid
  returning daily_goal_progress_minutes into v_daily;

  insert into public.user_daily_activity(user_id, activity_date, minutes, xp, events, last_source, updated_at)
  values (v_uid, v_today, v_minutes, v_xp, 1, v_source, now())
  on conflict (user_id, activity_date) do update set
    minutes = public.user_daily_activity.minutes + excluded.minutes,
    xp = public.user_daily_activity.xp + excluded.xp,
    events = public.user_daily_activity.events + 1,
    last_source = excluded.last_source,
    updated_at = now();

  return jsonb_build_object('streak_days',v_streak,'xp_added',v_xp,
    'daily_goal_progress_minutes',v_daily,'total_active_days',v_total_days,
    'activity_date',v_today,'source',v_source);
end;
$$;

grant execute on function public.record_my_learning_activity(integer,integer,text) to authenticated;
