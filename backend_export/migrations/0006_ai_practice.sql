-- FluentX — AI Practice
-- `system_prompt` is only ever read by the ai-practice-chat Edge
-- Function (service role) — never selected by the client, keeping
-- scenario prompt engineering server-side.

create table if not exists public.ai_practice_scenarios (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  category text not null,
  description text not null,
  system_prompt text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.ai_practice_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  scenario_id uuid not null references public.ai_practice_scenarios (id),
  transcript jsonb not null default '[]'::jsonb,
  accuracy_score integer,
  fluency_notes text,
  corrected_sentences jsonb not null default '[]'::jsonb,
  started_at timestamptz not null default now(),
  ended_at timestamptz
);

alter table public.ai_practice_scenarios enable row level security;
alter table public.ai_practice_sessions enable row level security;

drop policy if exists "Authenticated users can read scenarios" on public.ai_practice_scenarios;
create policy "Authenticated users can read scenarios"
  on public.ai_practice_scenarios for select
  to authenticated
  using (true);
-- Note: system_prompt is exposed by this policy at the row level, but
-- the Flutter client's PracticeScenario model never selects/parses
-- that column — only the Edge Function (service role) reads it. If
-- stricter defense-in-depth is wanted later, split system_prompt into
-- a separate table with no client-facing SELECT policy at all.

drop policy if exists "Users can insert own sessions" on public.ai_practice_sessions;
create policy "Users can insert own sessions"
  on public.ai_practice_sessions for insert
  with check (auth.uid() = user_id);

drop policy if exists "Users can read own sessions" on public.ai_practice_sessions;
create policy "Users can read own sessions"
  on public.ai_practice_sessions for select
  using (auth.uid() = user_id);
-- No client UPDATE policy: transcript/scores are written only by the
-- Edge Function via the service role (same reasoning as writing_submissions).

-- Seed scenarios
insert into public.ai_practice_scenarios (title, category, description, system_prompt) values
  (
    'Free Conversation',
    'General',
    'Chat about anything — great for warming up.',
    'You are a friendly, encouraging English conversation partner for an Indian professional practicing spoken English. Keep replies short (2-3 sentences), ask a natural follow-up question, and keep the conversation flowing naturally on any topic the user raises.'
  ),
  (
    'Business Meeting Roleplay',
    'Business',
    'Practice leading a status update meeting.',
    'You are a colleague in a business meeting roleplay. The user is presenting a project status update. Respond as a professional colleague would — ask clarifying questions about timelines, risks, or next steps. Keep replies concise and professional.'
  ),
  (
    'Job Interview Roleplay',
    'Interview',
    'Practice answering common interview questions.',
    'You are a friendly but professional job interviewer. Ask the user one common interview question at a time (e.g. tell me about yourself, strengths/weaknesses, why this role), listen to their answer, then ask a natural follow-up or move to the next question. Keep your turns brief.'
  ),
  (
    'Ordering Food',
    'Casual',
    'Practice everyday conversational English.',
    'You are a waiter at a casual restaurant. Take the user''s order, ask about drink choices, dietary preferences, and confirm the order back to them. Keep the tone light and casual.'
  ),
  (
    'Presentation Practice',
    'Business',
    'Practice explaining ideas clearly and confidently.',
    'You are an attentive audience member listening to the user present an idea or project. After they speak, ask one thoughtful clarifying question and give one brief piece of encouraging feedback on clarity.'
  )
on conflict do nothing;
