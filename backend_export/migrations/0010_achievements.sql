-- FluentX — Achievements
-- Aggregates real progress data server-side so unlock thresholds
-- (7-day streak, 10 AI chats, 1000 practice minutes, 500 words
-- mastered) are computed consistently in one place.

create or replace function public.get_achievement_stats(p_user_id uuid)
returns table (
  streak_days integer,
  ai_session_count integer,
  total_practice_minutes integer,
  vocabulary_mastered_count integer
)
language plpgsql
stable
as $$
declare
  v_streak_days integer;
  v_ai_session_count integer;
  v_total_minutes integer;
  v_mastered integer;
begin
  select coalesce(streak_days, 0) into v_streak_days
    from public.user_home_stats where user_id = p_user_id;

  select count(*) into v_ai_session_count
    from public.ai_practice_sessions
    where user_id = p_user_id and ended_at is not null;

  select coalesce(sum(extract(epoch from (ended_at - started_at)) / 60), 0)::integer
    into v_total_minutes
    from public.ai_practice_sessions
    where user_id = p_user_id and ended_at is not null;

  select count(*) into v_mastered
    from public.user_vocabulary_progress
    where user_id = p_user_id and repetition >= 2;

  return query select
    coalesce(v_streak_days, 0),
    coalesce(v_ai_session_count, 0),
    coalesce(v_total_minutes, 0),
    coalesce(v_mastered, 0);
end;
$$;

grant execute on function public.get_achievement_stats(uuid) to authenticated;
