-- FluentX — Grammar lessons, quiz questions, mistake tracking

create table if not exists public.grammar_lessons (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  explanation text not null,
  category text not null, -- e.g. 'Tenses', 'Articles', 'Prepositions'
  order_index integer not null default 0,
  created_at timestamptz not null default now()
);

create table if not exists public.grammar_questions (
  id uuid primary key default gen_random_uuid(),
  lesson_id uuid not null references public.grammar_lessons (id) on delete cascade,
  question_text text not null,
  options text[] not null,
  correct_index integer not null,
  created_at timestamptz not null default now()
);

-- One row per (user, category) — incremented on every wrong answer.
-- Feeds the Grammar Accuracy component of Communication DNA (Sprint 5)
-- and "adaptive difficulty" (surface weak categories more often).
create table if not exists public.user_grammar_mistakes (
  user_id uuid not null references auth.users (id) on delete cascade,
  category text not null,
  mistake_count integer not null default 0,
  updated_at timestamptz not null default now(),
  primary key (user_id, category)
);

alter table public.grammar_lessons enable row level security;
alter table public.grammar_questions enable row level security;
alter table public.user_grammar_mistakes enable row level security;

drop policy if exists "Authenticated users can read lessons" on public.grammar_lessons;
create policy "Authenticated users can read lessons"
  on public.grammar_lessons for select
  to authenticated
  using (true);

drop policy if exists "Authenticated users can read questions" on public.grammar_questions;
create policy "Authenticated users can read questions"
  on public.grammar_questions for select
  to authenticated
  using (true);

drop policy if exists "Users manage own mistake stats" on public.user_grammar_mistakes;
create policy "Users manage own mistake stats"
  on public.user_grammar_mistakes for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- Increment-or-insert helper, called once per wrong answer instead of
-- a client-side read-then-write (avoids a race between two devices).
create or replace function public.increment_grammar_mistake(
  p_user_id uuid,
  p_category text
)
returns void
language sql
as $$
  insert into public.user_grammar_mistakes (user_id, category, mistake_count, updated_at)
  values (p_user_id, p_category, 1, now())
  on conflict (user_id, category)
  do update set
    mistake_count = public.user_grammar_mistakes.mistake_count + 1,
    updated_at = now();
$$;

grant execute on function public.increment_grammar_mistake(uuid, text) to authenticated;

-- Seed content
with lesson_1 as (
  insert into public.grammar_lessons (title, explanation, category, order_index)
  values (
    'Present Simple vs Present Continuous',
    'Use the present simple for habits, facts, and routines ("I work every day"). Use the present continuous for actions happening right now or temporary situations ("I am working right now").',
    'Tenses',
    1
  )
  returning id
),
lesson_2 as (
  insert into public.grammar_lessons (title, explanation, category, order_index)
  values (
    'A, An, and The',
    'Use "a"/"an" for a non-specific, singular noun ("a book"). Use "an" before a vowel sound ("an hour"). Use "the" when the noun is specific or already known to the listener ("the book on the table").',
    'Articles',
    2
  )
  returning id
),
lesson_3 as (
  insert into public.grammar_lessons (title, explanation, category, order_index)
  values (
    'Prepositions of Time: In, On, At',
    'Use "in" for months/years ("in June"), "on" for days/dates ("on Monday"), and "at" for specific times ("at 5 PM").',
    'Prepositions',
    3
  )
  returning id
)
insert into public.grammar_questions (lesson_id, question_text, options, correct_index)
select id, question_text, options, correct_index
from (
  select (select id from lesson_1) as id,
    'She ___ to the gym every morning.' as question_text,
    array['is going', 'goes', 'go', 'gone'] as options,
    1 as correct_index
  union all
  select (select id from lesson_1),
    'Look! It ___ outside right now.',
    array['rains', 'is raining', 'rain', 'rained'],
    1
  union all
  select (select id from lesson_2),
    'I saw ___ elephant at the zoo yesterday.',
    array['a', 'an', 'the', '(no article)'],
    1
  union all
  select (select id from lesson_2),
    'Can you pass me ___ salt, please?',
    array['a', 'an', 'the', '(no article)'],
    2
  union all
  select (select id from lesson_3),
    'The meeting is ___ Monday ___ 10 AM.',
    array['in / on', 'on / at', 'at / in', 'on / on'],
    1
  union all
  select (select id from lesson_3),
    'Her birthday is ___ March.',
    array['in', 'on', 'at', 'for'],
    0
) as questions
on conflict do nothing;
