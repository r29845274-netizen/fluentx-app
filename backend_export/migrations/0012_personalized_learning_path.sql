-- FluentX — Personalized onboarding, placement test, 60-week A1→C1 learning path
-- Safe source migration. Designed to be idempotent.

begin;

create table if not exists public.user_learning_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  audience_type text not null default 'general_learner',
  goal text not null default 'general_fluency',
  native_language text not null default 'hi',
  current_cefr_level text not null default 'A1',
  current_week integer not null default 1 check (current_week between 1 and 60),
  placement_score numeric(5,2),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.learning_path_weeks (
  week_number integer primary key check (week_number between 1 and 60),
  cefr_level text not null check (cefr_level in ('A1','A2','B1','B2','C1')),
  title text not null,
  focus text not null,
  outcome text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.learning_path_lessons (
  id uuid primary key default gen_random_uuid(),
  week_number integer not null references public.learning_path_weeks(week_number) on delete cascade,
  day_number integer not null check (day_number between 1 and 5),
  lesson_type text not null,
  title text not null,
  instructions text not null,
  estimated_minutes integer not null default 15,
  unique (week_number, day_number)
);

create table if not exists public.user_learning_week_progress (
  user_id uuid not null references auth.users(id) on delete cascade,
  week_number integer not null references public.learning_path_weeks(week_number) on delete cascade,
  completion_percent numeric(5,2) not null default 0 check (completion_percent between 0 and 100),
  mastery_score numeric(5,2) check (mastery_score between 0 and 100),
  status text not null default 'not_started' check (status in ('not_started','in_progress','completed','needs_review')),
  last_activity_at timestamptz,
  primary key (user_id, week_number)
);

create table if not exists public.placement_questions (
  id uuid primary key default gen_random_uuid(),
  question_type text not null check (question_type in ('mcq','speaking')),
  skill text not null,
  cefr_level text not null check (cefr_level in ('A1','A2','B1','B2','C1')),
  difficulty_rank integer not null default 1,
  prompt text not null,
  options text[] not null default '{}',
  correct_index integer,
  sequence_no integer not null unique,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.placement_attempts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  final_score numeric(5,2),
  assigned_level text,
  start_week integer,
  started_at timestamptz not null default now(),
  completed_at timestamptz
);

create table if not exists public.placement_answers (
  attempt_id uuid not null references public.placement_attempts(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  question_id uuid not null references public.placement_questions(id) on delete cascade,
  selected_index integer,
  spoken_text text,
  speaking_score integer check (speaking_score between 0 and 100),
  speaking_feedback text,
  created_at timestamptz not null default now(),
  primary key (attempt_id, question_id)
);

-- RLS
alter table public.user_learning_profiles enable row level security;
alter table public.learning_path_weeks enable row level security;
alter table public.learning_path_lessons enable row level security;
alter table public.user_learning_week_progress enable row level security;
alter table public.placement_questions enable row level security;
alter table public.placement_attempts enable row level security;
alter table public.placement_answers enable row level security;

drop policy if exists "Users read own learning profile" on public.user_learning_profiles;
create policy "Users read own learning profile" on public.user_learning_profiles for select to authenticated using (auth.uid() = user_id);
drop policy if exists "Users insert own learning profile" on public.user_learning_profiles;
create policy "Users insert own learning profile" on public.user_learning_profiles for insert to authenticated with check (auth.uid() = user_id);
drop policy if exists "Users update own learning profile" on public.user_learning_profiles;
create policy "Users update own learning profile" on public.user_learning_profiles for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "Authenticated users read learning weeks" on public.learning_path_weeks;
create policy "Authenticated users read learning weeks" on public.learning_path_weeks for select to authenticated using (true);
drop policy if exists "Authenticated users read learning lessons" on public.learning_path_lessons;
create policy "Authenticated users read learning lessons" on public.learning_path_lessons for select to authenticated using (true);

drop policy if exists "Users manage own learning progress" on public.user_learning_week_progress;
create policy "Users manage own learning progress" on public.user_learning_week_progress for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "Authenticated users read placement questions" on public.placement_questions;
create policy "Authenticated users read placement questions" on public.placement_questions for select to authenticated using (true);
drop policy if exists "Users insert own placement attempts" on public.placement_attempts;
create policy "Users insert own placement attempts" on public.placement_attempts for insert to authenticated with check (auth.uid() = user_id);
drop policy if exists "Users read own placement attempts" on public.placement_attempts;
create policy "Users read own placement attempts" on public.placement_attempts for select to authenticated using (auth.uid() = user_id);
drop policy if exists "Users insert own placement answers" on public.placement_answers;
create policy "Users insert own placement answers" on public.placement_answers for insert to authenticated with check (auth.uid() = user_id);
drop policy if exists "Users update own placement answers" on public.placement_answers;
create policy "Users update own placement answers" on public.placement_answers for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);
drop policy if exists "Users read own placement answers" on public.placement_answers;
create policy "Users read own placement answers" on public.placement_answers for select to authenticated using (auth.uid() = user_id);

-- Full 60-week path. A1-A2-B1 follows the approved FluentX curriculum; B2-C1 completes the path.
insert into public.learning_path_weeks (week_number, cefr_level, title, focus, outcome) values
(1,'A1','Introduction & Basic English','Introductions, essential words, be-verbs','Introduce yourself confidently'),
(2,'A1','Daily Life English','Routines, classroom language, simple present','Describe daily routines'),
(3,'A1','Family & Relationships','Family vocabulary, possessives','Talk about family'),
(4,'A1','Numbers, Time & Dates','Numbers, days, months, clock time','Tell schedules and dates'),
(5,'A1','Common Conversations','Meeting people, help, information','Handle basic social exchanges'),
(6,'A1','Basic Grammar Foundation','Nouns, pronouns, verbs, adjectives','Build correct simple sentences'),
(7,'A1','Present Tense Mastery','Present simple and continuous','Describe habits and current actions'),
(8,'A1','Listening Foundation','Short conversations and word recognition','Understand slow everyday speech'),
(9,'A1','Vocabulary Expansion','Food, places, actions, emotions','Grow daily vocabulary'),
(10,'A1','Speaking Confidence','Short answers and full sentences','Speak with fewer one-word answers'),
(11,'A1','Basic Writing','Messages, paragraphs, simple emails','Write clear short messages'),
(12,'A1','Beginner Level Review & Test','A1 integrated review','Demonstrate A1 foundation'),
(13,'A2','Building Strong Sentences','SVO, negatives, longer sentences','Build connected sentences'),
(14,'A2','Past Events','Simple past, regular and irregular verbs','Describe past experiences'),
(15,'A2','Future Plans','Will and going to','Explain plans and goals'),
(16,'A2','College & Classroom English','Assignments, projects, presentations','Participate in academic situations'),
(17,'A2','Social Conversation','Opinions, agreement, friendship','Maintain social conversations'),
(18,'A2','Travel English','Airport, hotel, directions, transport','Handle common travel situations'),
(19,'A2','Grammar Improvement','Articles, prepositions, conjunctions','Reduce common grammar errors'),
(20,'A2','Listening Improvement','Stories and faster conversations','Follow common spoken English'),
(21,'A2','Vocabulary Power','Education, technology, career, daily life','Use broader practical vocabulary'),
(22,'A2','Presentation Skills','Open, explain, conclude','Give a short structured presentation'),
(23,'A2','Writing Skills','Formal messages, emails, short essays','Write basic professional content'),
(24,'A2','Elementary Level Review & Test','A2 integrated review','Demonstrate A2 independence'),
(25,'B1','Advanced Sentence Building','Complex sentences and linking words','Express connected ideas'),
(26,'B1','Professional Communication','Formal requests and senior communication','Communicate politely at work or college'),
(27,'B1','Interview English Foundation','Introduction, strengths, goals','Answer core interview questions'),
(28,'B1','Storytelling Skills','Events, experiences, narrative flow','Tell a clear 3-minute story'),
(29,'B1','Vocabulary Upgrade','Career, technology, personality','Use more precise vocabulary'),
(30,'B1','Discussion Skills','Agree, disagree, reasons','Participate in discussions'),
(31,'B1','Presentation Mastery','Opening, body, conclusion, confidence','Deliver organized presentations'),
(32,'B1','Writing Improvement','Professional emails, applications, reports','Write workplace-ready documents'),
(33,'B1','Listening Advanced','Faster speech and accent exposure','Understand real-world conversations'),
(34,'B1','Fluency Training','Speed, pauses, thinking in English','Speak more continuously'),
(35,'B1','Real World Practice','College, job, group discussion','Transfer skills to real situations'),
(36,'B1','Intermediate Level Review & Test','B1 integrated review','Demonstrate independent communication'),
(37,'B2','Nuanced Opinions','Qualifying opinions, evidence, contrast','Express balanced viewpoints'),
(38,'B2','Workplace Meetings','Updates, blockers, action items, diplomacy','Lead and contribute to meetings'),
(39,'B2','Negotiation & Persuasion','Trade-offs, proposals, objections','Negotiate clearly and respectfully'),
(40,'B2','Advanced Interview Performance','STAR stories, leadership, conflict','Handle behavioral interviews'),
(41,'B2','Professional Networking','Introductions, follow-ups, small talk','Build professional relationships'),
(42,'B2','Data & Trend Communication','Charts, trends, comparisons','Explain data and insights'),
(43,'B2','Advanced Grammar Control','Conditionals, modals, relative clauses','Use complex grammar accurately'),
(44,'B2','Listening at Natural Speed','Meetings, podcasts, connected speech','Follow natural-speed English'),
(45,'B2','Executive Writing Basics','Concise emails, summaries, proposals','Write concise professional messages'),
(46,'B2','Public Speaking & Q&A','Signposting, emphasis, answering questions','Present and respond under pressure'),
(47,'B2','Conflict & Difficult Conversations','Disagreement, feedback, de-escalation','Handle sensitive conversations'),
(48,'B2','Upper-Intermediate Review & Test','B2 integrated review','Demonstrate confident B2 communication'),
(49,'C1','Precision & Style','Register, nuance, concise expression','Choose language precisely'),
(50,'C1','Strategic Communication','Stakeholder framing and influence','Adapt messages to audience and purpose'),
(51,'C1','Advanced Leadership English','Delegation, coaching, alignment','Lead complex professional conversations'),
(52,'C1','Complex Problem Solving','Hypotheses, trade-offs, recommendations','Explain complex reasoning clearly'),
(53,'C1','High-Stakes Presentations','Narrative, executive presence, persuasion','Deliver persuasive high-stakes talks'),
(54,'C1','Advanced Listening & Inference','Implicit meaning, tone, stance','Infer meaning beyond literal words'),
(55,'C1','Advanced Writing & Editing','Reports, proposals, tone editing','Produce polished professional writing'),
(56,'C1','Cross-Cultural Communication','Diplomacy, idiom awareness, context','Communicate effectively across cultures'),
(57,'C1','Debate & Critical Discussion','Argument, rebuttal, synthesis','Defend and refine complex viewpoints'),
(58,'C1','Media & Thought Leadership','Panels, interviews, professional posts','Communicate publicly with authority'),
(59,'C1','Personal Communication Mastery','Weak-area repair and advanced simulation','Perform consistently across skills'),
(60,'C1','C1 Capstone & Final Assessment','Integrated real-world assessment','Demonstrate advanced FluentX mastery')
on conflict (week_number) do update set
  cefr_level=excluded.cefr_level,
  title=excluded.title,
  focus=excluded.focus,
  outcome=excluded.outcome;

-- Five structured lessons per week = 300 lesson records.
insert into public.learning_path_lessons (week_number, day_number, lesson_type, title, instructions, estimated_minutes)
select
  w.week_number,
  d.day_number,
  case d.day_number
    when 1 then 'Learn'
    when 2 then 'Vocabulary & Grammar'
    when 3 then 'Listening'
    when 4 then 'Speaking / Writing'
    else 'Review & Quiz'
  end,
  w.title || ' — ' || case d.day_number
    when 1 then 'Core Lesson'
    when 2 then 'Language Builder'
    when 3 then 'Listening Drill'
    when 4 then 'Production Practice'
    else 'Weekly Review'
  end,
  case d.day_number
    when 1 then 'Learn the core concepts for: ' || w.focus || '. Finish with three example sentences.'
    when 2 then 'Build vocabulary and grammar connected to: ' || w.focus || '. Complete targeted practice and corrections.'
    when 3 then 'Listen for key meaning, details, and useful phrases related to: ' || w.focus || '.'
    when 4 then 'Produce English actively through speaking or writing. Goal: ' || w.outcome || '.'
    else 'Review the week, correct mistakes, complete the quiz, and identify one weak area for revision.'
  end,
  case when d.day_number = 5 then 20 else 15 end
from public.learning_path_weeks w
cross join (values (1),(2),(3),(4),(5)) as d(day_number)
on conflict (week_number, day_number) do update set
  lesson_type=excluded.lesson_type,
  title=excluded.title,
  instructions=excluded.instructions,
  estimated_minutes=excluded.estimated_minutes;

-- Placement question bank: progressively harder grammar/usage plus one speaking item per CEFR band.
insert into public.placement_questions (question_type, skill, cefr_level, difficulty_rank, prompt, options, correct_index, sequence_no, is_active) values
('mcq','grammar','A1',1,'Choose the correct sentence.',array['She are a student.','She is a student.','She be a student.','She am a student.'],1,1,true),
('mcq','vocabulary','A1',1,'What does “borrow” mean?',array['Give something forever','Take something temporarily and return it','Buy something','Break something'],1,2,true),
('mcq','grammar','A1',2,'I ___ to college every day.',array['go','goes','am go','going'],0,3,true),
('speaking','speaking','A1',2,'Introduce yourself and describe one thing you do every day.',array[]::text[],null,4,true),
('mcq','grammar','A2',3,'Yesterday we ___ the client at 3 PM.',array['meet','met','have meet','are meeting'],1,5,true),
('mcq','grammar','A2',3,'I am going to ___ a new course next month.',array['started','starting','start','starts'],2,6,true),
('mcq','vocabulary','A2',3,'If a train is delayed, it is ___.',array['earlier than planned','later than planned','cancelled forever','empty'],1,7,true),
('speaking','speaking','A2',4,'Describe what you did last weekend and one plan for next weekend.',array[]::text[],null,8,true),
('mcq','grammar','B1',5,'If I ___ more time, I would practice every day.',array['have','had','will have','am having'],1,9,true),
('mcq','usage','B1',5,'Choose the most professional request.',array['Send me the report now.','Could you please send me the report by 4 PM?','You send report.','Report, please.'],1,10,true),
('mcq','grammar','B1',6,'The project, ___ started in April, is almost complete.',array['who','which','where','what'],1,11,true),
('speaking','speaking','B1',6,'Explain a challenge you faced and how you solved it.',array[]::text[],null,12,true),
('mcq','usage','B2',7,'Choose the sentence that best qualifies an opinion.',array['This plan is perfect.','This plan is wrong.','While the plan has clear benefits, the implementation risk should not be ignored.','Plan good but risk.'],2,13,true),
('mcq','grammar','B2',7,'Had we known about the delay, we ___ the schedule earlier.',array['change','would change','would have changed','changed'],2,14,true),
('mcq','vocabulary','B2',8,'“Mitigate a risk” most nearly means:',array['Ignore a risk','Increase a risk','Reduce the likelihood or impact of a risk','Describe a risk dramatically'],2,15,true),
('speaking','speaking','B2',8,'Give a balanced opinion on remote work, including one benefit, one drawback, and your recommendation.',array[]::text[],null,16,true),
('mcq','usage','C1',9,'Choose the most precise executive summary sentence.',array['Sales went down because many things happened.','Revenue declined 8% primarily due to lower repeat purchases, while acquisition remained stable.','Sales bad this quarter.','There were issues with revenue and customers.'],1,17,true),
('mcq','vocabulary','C1',9,'“A nuanced argument” is one that:',array['Uses only simple words','Recognizes complexity and subtle distinctions','Avoids evidence','Is intentionally confusing'],1,18,true),
('mcq','grammar','C1',10,'Choose the most natural sentence.',array['Not only the team met the deadline, but quality also improved.','Not only did the team meet the deadline, but quality also improved.','Not only did meet the team deadline, but quality improved also.','The team not only did deadline but quality.'],1,19,true),
('speaking','speaking','C1',10,'Present a concise recommendation for a difficult workplace decision, acknowledge trade-offs, and justify your preferred option.',array[]::text[],null,20,true)
on conflict (sequence_no) do update set
  question_type=excluded.question_type,
  skill=excluded.skill,
  cefr_level=excluded.cefr_level,
  difficulty_rank=excluded.difficulty_rank,
  prompt=excluded.prompt,
  options=excluded.options,
  correct_index=excluded.correct_index,
  is_active=excluded.is_active;

-- RPC used by the personalized onboarding UI.
create or replace function public.save_my_onboarding_profile(
  p_audience_type text,
  p_goal text,
  p_native_language text default 'hi'
)
returns void
language plpgsql
security invoker
as $$
begin
  if auth.uid() is null then raise exception 'Not authenticated'; end if;
  insert into public.user_learning_profiles (user_id, audience_type, goal, native_language)
  values (auth.uid(), p_audience_type, p_goal, coalesce(nullif(p_native_language,''),'hi'))
  on conflict (user_id) do update set
    audience_type=excluded.audience_type,
    goal=excluded.goal,
    native_language=excluded.native_language,
    updated_at=now();
end;
$$;

grant execute on function public.save_my_onboarding_profile(text,text,text) to authenticated;

create or replace function public.get_my_onboarding_state()
returns jsonb
language sql
stable
security invoker
as $$
  select jsonb_build_object(
    'audience_type', coalesce(p.audience_type,'general_learner'),
    'goal', coalesce(p.goal,'general_fluency'),
    'native_language', coalesce(p.native_language,'hi'),
    'current_cefr_level', coalesce(p.current_cefr_level,'A1'),
    'current_week', coalesce(p.current_week,1),
    'placement_score', p.placement_score
  )
  from (select auth.uid() as uid) u
  left join public.user_learning_profiles p on p.user_id=u.uid;
$$;

grant execute on function public.get_my_onboarding_state() to authenticated;

create or replace function public.get_my_learning_path()
returns table (
  week_number integer,
  cefr_level text,
  title text,
  focus text,
  outcome text,
  status text,
  completion_percent numeric,
  mastery_score numeric
)
language sql
stable
security invoker
as $$
  select
    w.week_number,
    w.cefr_level,
    w.title,
    w.focus,
    w.outcome,
    coalesce(p.status,'not_started'),
    coalesce(p.completion_percent,0),
    p.mastery_score
  from public.learning_path_weeks w
  left join public.user_learning_week_progress p
    on p.week_number=w.week_number and p.user_id=auth.uid()
  order by w.week_number;
$$;

grant execute on function public.get_my_learning_path() to authenticated;

create or replace function public.get_my_current_week_lessons()
returns table (
  lesson_id uuid,
  week_number integer,
  day_number integer,
  lesson_type text,
  title text,
  instructions text,
  estimated_minutes integer
)
language sql
stable
security invoker
as $$
  select l.id,l.week_number,l.day_number,l.lesson_type,l.title,l.instructions,l.estimated_minutes
  from public.learning_path_lessons l
  where l.week_number=coalesce((select current_week from public.user_learning_profiles where user_id=auth.uid()),1)
  order by l.day_number;
$$;

grant execute on function public.get_my_current_week_lessons() to authenticated;

create or replace function public.score_my_placement_attempt(p_attempt_id uuid)
returns table (assigned_level text, final_score numeric, start_week integer)
language plpgsql
security definer
set search_path = public, auth
as $$
declare
  v_user uuid := auth.uid();
  v_score numeric;
  v_level text;
  v_week integer;
begin
  if v_user is null then raise exception 'Not authenticated'; end if;
  if not exists (select 1 from public.placement_attempts where id=p_attempt_id and user_id=v_user) then
    raise exception 'Placement attempt not found';
  end if;

  select coalesce(avg(
    case
      when q.question_type='speaking' then coalesce(a.speaking_score,0)::numeric
      when a.selected_index=q.correct_index then 100::numeric
      else 0::numeric
    end
  ),0)
  into v_score
  from public.placement_questions q
  left join public.placement_answers a
    on a.question_id=q.id and a.attempt_id=p_attempt_id and a.user_id=v_user
  where q.is_active=true;

  if v_score < 35 then v_level:='A1'; v_week:=1;
  elsif v_score < 50 then v_level:='A2'; v_week:=13;
  elsif v_score < 65 then v_level:='B1'; v_week:=25;
  elsif v_score < 80 then v_level:='B2'; v_week:=37;
  else v_level:='C1'; v_week:=49;
  end if;

  update public.placement_attempts
  set final_score=round(v_score,2), assigned_level=v_level, start_week=v_week, completed_at=now()
  where id=p_attempt_id and user_id=v_user;

  insert into public.user_learning_profiles (user_id,current_cefr_level,current_week,placement_score)
  values (v_user,v_level,v_week,round(v_score,2))
  on conflict (user_id) do update set
    current_cefr_level=excluded.current_cefr_level,
    current_week=excluded.current_week,
    placement_score=excluded.placement_score,
    updated_at=now();

  insert into public.user_learning_week_progress(user_id,week_number,status,completion_percent)
  values(v_user,v_week,'in_progress',0)
  on conflict(user_id,week_number) do update set status='in_progress', last_activity_at=now();

  return query select v_level, round(v_score,2), v_week;
end;
$$;

grant execute on function public.score_my_placement_attempt(uuid) to authenticated;

-- Adaptive weak-area recommendation. It uses existing grammar/listening/vocabulary data when present.
create or replace function public.get_my_learning_recommendation()
returns jsonb
language plpgsql
stable
security invoker
as $$
declare
  v_user uuid := auth.uid();
  v_grammar text;
  v_grammar_mistakes integer := 0;
  v_listening numeric;
  v_due integer := 0;
begin
  select category,mistake_count into v_grammar,v_grammar_mistakes
  from public.user_grammar_mistakes
  where user_id=v_user
  order by mistake_count desc, updated_at desc
  limit 1;

  select avg(score) into v_listening
  from public.user_listening_progress
  where user_id=v_user;

  select count(*) into v_due
  from public.user_vocabulary_progress
  where user_id=v_user and due_date<=current_date;

  if coalesce(v_listening,100) < 65 then
    return jsonb_build_object('recommended_skill','Listening','title','Strengthen listening comprehension','reason','Your recent listening average is below the mastery target.');
  elsif coalesce(v_grammar_mistakes,0) >= 3 then
    return jsonb_build_object('recommended_skill','Grammar','title','Review '||coalesce(v_grammar,'grammar'),'reason','This is currently your most repeated grammar mistake area.');
  elsif v_due >= 5 then
    return jsonb_build_object('recommended_skill','Vocabulary','title','Complete your vocabulary review','reason',v_due||' review items are currently due.');
  else
    return jsonb_build_object('recommended_skill','Current Week','title','Continue your personalized learning path','reason','No major weak area is currently blocking your progress.');
  end if;
end;
$$;

grant execute on function public.get_my_learning_recommendation() to authenticated;

commit;
