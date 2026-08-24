-- Cross-session learning-memory foundation for Maya.
-- Stores concise learner preferences and coaching focus for future personalized sessions.

create table if not exists public.maya_learning_memory (
  user_id uuid primary key references auth.users(id) on delete cascade,
  memory_note text not null default '',
  preferred_topics text[] not null default '{}',
  focus_area text,
  updated_at timestamptz not null default now()
);

alter table public.maya_learning_memory enable row level security;
drop policy if exists "Users read own Maya learning memory" on public.maya_learning_memory;
create policy "Users read own Maya learning memory"
  on public.maya_learning_memory for select to authenticated
  using ((select auth.uid()) = user_id);
revoke insert, update, delete on public.maya_learning_memory from anon, authenticated;
grant select on public.maya_learning_memory to authenticated;
