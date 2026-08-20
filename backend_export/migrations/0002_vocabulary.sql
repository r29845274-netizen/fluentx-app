-- FluentX — Vocabulary (spaced repetition)

create table if not exists public.vocabulary_words (
  id uuid primary key default gen_random_uuid(),
  word text not null,
  definition text not null,
  example_sentence text not null,
  category text not null, -- 'Business' | 'Interview' | 'Casual' | 'Academic'
  created_at timestamptz not null default now()
);

create table if not exists public.user_vocabulary_progress (
  user_id uuid not null references auth.users (id) on delete cascade,
  word_id uuid not null references public.vocabulary_words (id) on delete cascade,
  repetition integer not null default 0,
  ease_factor numeric(4, 2) not null default 2.5,
  interval_days integer not null default 0,
  due_date date not null default current_date,
  last_reviewed_at timestamptz,
  primary key (user_id, word_id)
);

-- Server-side "what's due to review right now" query — combines words
-- the user has never seen (no progress row) with words whose SM-2
-- due_date has arrived, ordered so brand-new words come first.
create or replace function public.get_due_vocabulary_words(
  p_user_id uuid,
  p_limit integer default 10
)
returns table (
  word_id uuid,
  word text,
  definition text,
  example_sentence text,
  category text,
  repetition integer,
  ease_factor numeric,
  interval_days integer,
  due_date date
)
language sql
stable
as $$
  select
    w.id as word_id,
    w.word,
    w.definition,
    w.example_sentence,
    w.category,
    coalesce(p.repetition, 0),
    coalesce(p.ease_factor, 2.5),
    coalesce(p.interval_days, 0),
    coalesce(p.due_date, current_date)
  from public.vocabulary_words w
  left join public.user_vocabulary_progress p
    on p.word_id = w.id and p.user_id = p_user_id
  where p.due_date is null or p.due_date <= current_date
  order by (p.due_date is null) desc, p.due_date asc, w.created_at asc
  limit p_limit;
$$;

grant execute on function public.get_due_vocabulary_words(uuid, integer) to authenticated;

alter table public.vocabulary_words enable row level security;
alter table public.user_vocabulary_progress enable row level security;

drop policy if exists "Authenticated users can read vocabulary" on public.vocabulary_words;
create policy "Authenticated users can read vocabulary"
  on public.vocabulary_words for select
  to authenticated
  using (true);

drop policy if exists "Users manage own vocabulary progress" on public.user_vocabulary_progress;
create policy "Users manage own vocabulary progress"
  on public.user_vocabulary_progress for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- Seed content
insert into public.vocabulary_words (word, definition, example_sentence, category) values
  ('Leverage', 'To use something to maximum advantage.', 'We should leverage our existing customer base to launch the new product.', 'Business'),
  ('Synergy', 'The combined effect of two things working together, greater than the sum of their parts.', 'The merger created strong synergy between the two engineering teams.', 'Business'),
  ('Deadline', 'The latest time or date by which something must be completed.', 'The report deadline is this Friday at 5 PM.', 'Business'),
  ('Stakeholder', 'A person with an interest or concern in a business or project.', 'We need sign-off from every stakeholder before launch.', 'Business'),
  ('Articulate', 'Able to express thoughts and ideas clearly and effectively.', 'She gave an articulate answer to a difficult interview question.', 'Interview'),
  ('Strength', 'A good or beneficial quality of a person.', 'My biggest strength is staying calm under pressure.', 'Interview'),
  ('Weakness', 'A disadvantage or fault in a person.', 'I used to struggle with public speaking, but I have been working on it.', 'Interview'),
  ('Qualification', 'A quality or accomplishment that makes someone suitable for a job.', 'Her qualifications made her the strongest candidate.', 'Interview'),
  ('Grab', 'To take or seize something quickly.', 'Let''s grab a coffee before the meeting starts.', 'Casual'),
  ('Hang out', 'To spend time relaxing or socializing.', 'We usually hang out at the park on weekends.', 'Casual'),
  ('Catch up', 'To meet and share news after not seeing someone for a while.', 'Let''s catch up over lunch sometime next week.', 'Casual'),
  ('Awesome', 'Extremely impressive or daunting; very good.', 'That was an awesome presentation!', 'Casual'),
  ('Hypothesis', 'A proposed explanation made on the basis of limited evidence.', 'The researchers tested their hypothesis with a controlled experiment.', 'Academic'),
  ('Analyze', 'To examine something in detail to understand it better.', 'Students were asked to analyze the poem''s structure.', 'Academic'),
  ('Citation', 'A quotation from or reference to a source.', 'Every claim in the essay needs a proper citation.', 'Academic'),
  ('Coherent', 'Logical and consistent; forming a unified whole.', 'The essay needs a more coherent argument.', 'Academic')
on conflict do nothing;
