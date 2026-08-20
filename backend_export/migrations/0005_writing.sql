-- FluentX — Writing
-- AI scoring (grammar/clarity/structure/tone) is written back to
-- `writing_submissions` by the `score-writing` Supabase Edge Function
-- (supabase/functions/score-writing), which runs with the service
-- role and calls OpenAI — never from the client directly, per the
-- "AI keys never exposed client-side" rule from the master spec.

create table if not exists public.writing_prompts (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  category text not null, -- 'Email' | 'Cover Letter' | 'Essay' | 'Report' | 'LinkedIn Post'
  instructions text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.writing_submissions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  prompt_id uuid not null references public.writing_prompts (id),
  content text not null,
  grammar_score integer,
  clarity_score integer,
  structure_score integer,
  tone_score integer,
  ai_feedback text,
  scored_at timestamptz,
  created_at timestamptz not null default now()
);

alter table public.writing_prompts enable row level security;
alter table public.writing_submissions enable row level security;

drop policy if exists "Authenticated users can read prompts" on public.writing_prompts;
create policy "Authenticated users can read prompts"
  on public.writing_prompts for select to authenticated using (true);

-- Users can create/read their own submissions but NOT update the
-- score columns directly — only the Edge Function (service role,
-- which bypasses RLS entirely) writes scores. This stops a client
-- from just setting grammar_score = 100 on itself.
drop policy if exists "Users can insert own submissions" on public.writing_submissions;
create policy "Users can insert own submissions"
  on public.writing_submissions for insert
  with check (auth.uid() = user_id);

drop policy if exists "Users can read own submissions" on public.writing_submissions;
create policy "Users can read own submissions"
  on public.writing_submissions for select
  using (auth.uid() = user_id);

-- Seed content
insert into public.writing_prompts (title, category, instructions) values
  (
    'Request a Deadline Extension',
    'Email',
    'Write a professional email to your manager requesting a 3-day extension on a project deadline. Explain the reason briefly and propose a new date.'
  ),
  (
    'Cover Letter for a Marketing Role',
    'Cover Letter',
    'Write a short cover letter (150-200 words) for a Marketing Executive position, highlighting relevant skills and enthusiasm for the role.'
  ),
  (
    'Should Remote Work Be the Default?',
    'Essay',
    'Write a short persuasive essay (200-250 words) arguing for or against remote work becoming the default for office jobs.'
  ),
  (
    'Weekly Status Report',
    'Report',
    'Write a concise weekly status report for your team covering: what was completed, what is blocked, and next steps.'
  ),
  (
    'Announce a Career Milestone',
    'LinkedIn Post',
    'Write a LinkedIn post announcing a new certification or promotion, in a tone that is confident but not boastful.'
  )
on conflict do nothing;
