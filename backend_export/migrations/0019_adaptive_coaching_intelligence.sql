-- FluentX adaptive coaching intelligence
-- Mirrors live Supabase migration adaptive_coaching_intelligence.

alter table if exists public.maya_learning_memory
  add column if not exists recurring_mistakes jsonb not null default '[]'::jsonb,
  add column if not exists recent_topics text[] not null default '{}',
  add column if not exists learner_summary text not null default '',
  add column if not exists last_session_at timestamptz;

create table if not exists public.learner_mistake_profile (
  user_id uuid not null references auth.users(id) on delete cascade,
  mistake_key text not null,
  category text not null check (category in ('grammar','vocabulary','pronunciation','fluency','phrasing','interview','other')),
  example text,
  correction text,
  source text not null default 'learning',
  occurrences integer not null default 1,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  primary key (user_id, mistake_key)
);

create table if not exists public.pronunciation_attempts (
  id bigserial primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  target_text text not null,
  recognized_text text not null default '',
  clarity_score integer not null check (clarity_score between 0 and 100),
  confidence_score numeric(5,4),
  weak_words text[] not null default '{}',
  created_at timestamptz not null default now()
);
create index if not exists pronunciation_attempts_user_created_idx on public.pronunciation_attempts(user_id,created_at desc);

create table if not exists public.daily_personalized_practice (
  user_id uuid not null references auth.users(id) on delete cascade,
  practice_date date not null,
  focus_title text not null,
  focus_summary text not null,
  items jsonb not null default '[]'::jsonb,
  completed_items integer not null default 0,
  generated_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (user_id,practice_date)
);

alter table public.learner_mistake_profile enable row level security;
alter table public.pronunciation_attempts enable row level security;
alter table public.daily_personalized_practice enable row level security;

drop policy if exists "Users read own mistake profile" on public.learner_mistake_profile;
create policy "Users read own mistake profile" on public.learner_mistake_profile for select to authenticated using ((select auth.uid())=user_id);
drop policy if exists "Users read own pronunciation attempts" on public.pronunciation_attempts;
create policy "Users read own pronunciation attempts" on public.pronunciation_attempts for select to authenticated using ((select auth.uid())=user_id);
drop policy if exists "Users read own daily practice" on public.daily_personalized_practice;
create policy "Users read own daily practice" on public.daily_personalized_practice for select to authenticated using ((select auth.uid())=user_id);

revoke insert,update,delete on public.learner_mistake_profile from anon,authenticated;
revoke insert,update,delete on public.pronunciation_attempts from anon,authenticated;
revoke insert,update,delete on public.daily_personalized_practice from anon,authenticated;
grant select on public.learner_mistake_profile to authenticated;
grant select on public.pronunciation_attempts to authenticated;
grant select on public.daily_personalized_practice to authenticated;

create or replace function public.record_my_learning_mistake(p_category text,p_mistake_key text,p_example text default null,p_correction text default null,p_source text default 'learning') returns void
language plpgsql security definer set search_path to 'public','pg_temp'
as $$
declare v_uid uuid:=auth.uid(); v_category text:=lower(trim(coalesce(p_category,''))); v_key text:=left(lower(trim(coalesce(p_mistake_key,''))),120); v_source text:=left(coalesce(nullif(trim(coalesce(p_source,'')),''),'learning'),64);
begin
 if v_uid is null then raise exception 'Authentication required' using errcode='42501'; end if;
 if v_category not in('grammar','vocabulary','pronunciation','fluency','phrasing','interview','other') then raise exception 'Invalid mistake category' using errcode='22023'; end if;
 if length(v_key)<2 then raise exception 'Mistake key is required' using errcode='22023'; end if;
 insert into public.learner_mistake_profile(user_id,mistake_key,category,example,correction,source,occurrences,first_seen_at,last_seen_at)
 values(v_uid,v_key,v_category,left(p_example,500),left(p_correction,500),v_source,1,now(),now())
 on conflict(user_id,mistake_key) do update set category=excluded.category,example=coalesce(excluded.example,public.learner_mistake_profile.example),correction=coalesce(excluded.correction,public.learner_mistake_profile.correction),source=excluded.source,occurrences=public.learner_mistake_profile.occurrences+1,last_seen_at=now();
end;$$;
grant execute on function public.record_my_learning_mistake(text,text,text,text,text) to authenticated;

create or replace function public.record_my_pronunciation_attempt(p_target_text text,p_recognized_text text,p_clarity_score integer,p_confidence_score numeric default null,p_weak_words text[] default '{}') returns jsonb
language plpgsql security definer set search_path to 'public','pg_temp'
as $$
declare v_uid uuid:=auth.uid(); v_score integer:=greatest(0,least(100,coalesce(p_clarity_score,0))); v_word text;
begin
 if v_uid is null then raise exception 'Authentication required' using errcode='42501'; end if;
 if length(trim(coalesce(p_target_text,'')))<2 then raise exception 'Target text is required' using errcode='22023'; end if;
 insert into public.pronunciation_attempts(user_id,target_text,recognized_text,clarity_score,confidence_score,weak_words)
 values(v_uid,left(p_target_text,500),left(coalesce(p_recognized_text,''),500),v_score,case when p_confidence_score is null then null else greatest(0,least(1,p_confidence_score)) end,coalesce(p_weak_words,'{}'));
 foreach v_word in array coalesce(p_weak_words,'{}') loop
  if length(trim(v_word))>=2 then
   insert into public.learner_mistake_profile(user_id,mistake_key,category,example,correction,source,occurrences,first_seen_at,last_seen_at)
   values(v_uid,'pronunciation:'||lower(trim(v_word)),'pronunciation',trim(v_word),null,'pronunciation_practice',1,now(),now())
   on conflict(user_id,mistake_key) do update set occurrences=public.learner_mistake_profile.occurrences+1,last_seen_at=now();
  end if;
 end loop;
 perform public.record_my_learning_activity(2,8,'pronunciation_practice');
 return jsonb_build_object('saved',true,'clarity_score',v_score,'weak_words',coalesce(p_weak_words,'{}'));
end;$$;
grant execute on function public.record_my_pronunciation_attempt(text,text,integer,numeric,text[]) to authenticated;

create or replace function public.get_my_daily_personalized_practice() returns jsonb
language plpgsql security definer set search_path to 'public','pg_temp'
as $$
declare v_uid uuid:=auth.uid(); v_date date:=(now() at time zone 'Asia/Kolkata')::date; v_existing public.daily_personalized_practice%rowtype; v_top record; v_items jsonb:='[]'::jsonb; v_title text:='Daily Confidence Boost'; v_summary text:='A short practice set based on your recent learning activity.'; v_i integer:=0;
begin
 if v_uid is null then raise exception 'Authentication required' using errcode='42501'; end if;
 select * into v_existing from public.daily_personalized_practice where user_id=v_uid and practice_date=v_date;
 if v_existing.user_id is not null then return jsonb_build_object('practice_date',v_existing.practice_date,'focus_title',v_existing.focus_title,'focus_summary',v_existing.focus_summary,'items',v_existing.items,'completed_items',v_existing.completed_items); end if;
 for v_top in select category,mistake_key,example,correction,occurrences from public.learner_mistake_profile where user_id=v_uid order by occurrences desc,last_seen_at desc limit 3 loop
  v_i:=v_i+1;
  if v_i=1 then
   v_title:=case v_top.category when 'pronunciation' then 'Speak More Clearly Today' when 'grammar' then 'Fix Your Most Common Grammar Mistake' when 'vocabulary' then 'Upgrade Your Everyday Vocabulary' when 'fluency' then 'Speak More Smoothly Today' when 'phrasing' then 'Sound More Natural Today' when 'interview' then 'Sharpen Your Interview English' else 'Made for You' end;
   v_summary:='Built from mistakes FluentX has seen more than once in your recent practice.';
  end if;
  v_items:=v_items||jsonb_build_array(jsonb_build_object('id','focus_'||v_i,'type',v_top.category,'title',case v_top.category when 'pronunciation' then 'Repeat the weak word clearly' when 'grammar' then 'Correct the sentence' when 'vocabulary' then 'Use a stronger word' when 'fluency' then 'Say it again without stopping' when 'phrasing' then 'Make it sound natural' when 'interview' then 'Answer with a stronger structure' else 'Practice this improvement' end,'prompt',coalesce(v_top.example,replace(v_top.mistake_key,':',' ')),'answer',v_top.correction,'reason','Seen '||v_top.occurrences||' time'||case when v_top.occurrences=1 then '' else 's' end));
 end loop;
 while jsonb_array_length(v_items)<5 loop
  v_i:=v_i+1;
  v_items:=v_items||jsonb_build_array(jsonb_build_object('id','daily_'||v_i,'type',case when v_i%2=0 then 'fluency' else 'phrasing' end,'title',case when v_i%2=0 then '30-second speaking challenge' else 'Natural English upgrade' end,'prompt',case when v_i%2=0 then 'Speak for 30 seconds about your day, work, study or goals without switching languages.' else 'Say one thought from your day in simple natural English, then improve it once.' end,'answer',null,'reason','Daily confidence practice'));
 end loop;
 insert into public.daily_personalized_practice(user_id,practice_date,focus_title,focus_summary,items) values(v_uid,v_date,v_title,v_summary,v_items) returning * into v_existing;
 return jsonb_build_object('practice_date',v_existing.practice_date,'focus_title',v_existing.focus_title,'focus_summary',v_existing.focus_summary,'items',v_existing.items,'completed_items',v_existing.completed_items);
end;$$;
grant execute on function public.get_my_daily_personalized_practice() to authenticated;

create or replace function public.complete_my_daily_personalized_item(p_item_id text) returns jsonb
language plpgsql security definer set search_path to 'public','pg_temp'
as $$
declare v_uid uuid:=auth.uid(); v_date date:=(now() at time zone 'Asia/Kolkata')::date; v_row public.daily_personalized_practice%rowtype; v_total integer;
begin
 if v_uid is null then raise exception 'Authentication required' using errcode='42501'; end if;
 select * into v_row from public.daily_personalized_practice where user_id=v_uid and practice_date=v_date for update;
 if v_row.user_id is null then perform public.get_my_daily_personalized_practice(); select * into v_row from public.daily_personalized_practice where user_id=v_uid and practice_date=v_date for update; end if;
 v_total:=jsonb_array_length(v_row.items);
 update public.daily_personalized_practice set completed_items=least(v_total,completed_items+1),updated_at=now() where user_id=v_uid and practice_date=v_date returning * into v_row;
 perform public.record_my_learning_activity(1,5,'personalized_daily_practice');
 return jsonb_build_object('completed_items',v_row.completed_items,'total_items',v_total,'all_complete',v_row.completed_items>=v_total);
end;$$;
grant execute on function public.complete_my_daily_personalized_item(text) to authenticated;
