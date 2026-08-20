alter table public.user_home_stats
  add column if not exists learning_goal text;
