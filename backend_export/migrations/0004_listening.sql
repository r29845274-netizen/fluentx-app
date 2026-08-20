-- FluentX — Listening
-- Audio is synthesized on-device from `transcript` via flutter_tts
-- (adjustable speech rate covers "native-speed + slowed variants"
-- without needing hosted audio files/CDN for the MVP). Swappable for
-- pre-recorded/Neural TTS audio later without changing this schema —
-- just add an `audio_url` column and prefer it when present.

create table if not exists public.listening_clips (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  category text not null,
  transcript text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.listening_questions (
  id uuid primary key default gen_random_uuid(),
  clip_id uuid not null references public.listening_clips (id) on delete cascade,
  question_text text not null,
  options text[] not null,
  correct_index integer not null,
  created_at timestamptz not null default now()
);

create table if not exists public.user_listening_progress (
  user_id uuid not null references auth.users (id) on delete cascade,
  clip_id uuid not null references public.listening_clips (id) on delete cascade,
  score numeric(5, 2) not null,
  completed_at timestamptz not null default now(),
  primary key (user_id, clip_id)
);

alter table public.listening_clips enable row level security;
alter table public.listening_questions enable row level security;
alter table public.user_listening_progress enable row level security;

drop policy if exists "Authenticated users can read clips" on public.listening_clips;
create policy "Authenticated users can read clips"
  on public.listening_clips for select to authenticated using (true);

drop policy if exists "Authenticated users can read listening questions" on public.listening_questions;
create policy "Authenticated users can read listening questions"
  on public.listening_questions for select to authenticated using (true);

drop policy if exists "Users manage own listening progress" on public.user_listening_progress;
create policy "Users manage own listening progress"
  on public.user_listening_progress for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- Seed content
with clip_1 as (
  insert into public.listening_clips (title, category, transcript)
  values (
    'Business Meeting Kickoff',
    'Business',
    'Good morning everyone, thanks for joining on time. Today we will review last quarter''s numbers and align on priorities for the next sprint. Let''s start with a quick round of updates from each team.'
  )
  returning id
),
clip_2 as (
  insert into public.listening_clips (title, category, transcript)
  values (
    'Casual Weekend Plans',
    'Casual',
    'Hey, do you have any plans this weekend? I was thinking we could grab brunch on Saturday and maybe catch a movie in the evening. Let me know what works for you.'
  )
  returning id
),
clip_3 as (
  insert into public.listening_clips (title, category, transcript)
  values (
    'Job Interview: Tell Me About Yourself',
    'Interview',
    'Thanks for coming in today. To start, could you walk me through your background and what led you to apply for this role? Feel free to highlight any projects you are proud of.'
  )
  returning id
)
insert into public.listening_questions (clip_id, question_text, options, correct_index)
select id, question_text, options, correct_index
from (
  select (select id from clip_1) as id,
    'What will the team review first?' as question_text,
    array['Next year''s budget', 'Last quarter''s numbers', 'A new hire', 'Office relocation'] as options,
    1 as correct_index
  union all
  select (select id from clip_2),
    'What does the speaker suggest doing on Saturday?',
    array['Going hiking', 'Brunch', 'Studying', 'Working overtime'],
    1
  union all
  select (select id from clip_3),
    'What is the interviewer asking the candidate to do?',
    array['Sign a contract', 'Describe their background', 'Take a test', 'Leave a reference'],
    1
) as questions
on conflict do nothing;
