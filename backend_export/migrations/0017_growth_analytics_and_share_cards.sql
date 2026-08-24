-- FluentX acquisition/retention analytics + share-card stats.
-- Mirrors production migration growth_analytics_and_share_cards.

create table if not exists public.user_acquisition_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  first_source text not null default 'organic',
  first_campaign text,
  referral_code text,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.user_acquisition_profiles enable row level security;
drop policy if exists "Users read own acquisition profile" on public.user_acquisition_profiles;
create policy "Users read own acquisition profile" on public.user_acquisition_profiles
  for select to authenticated using ((select auth.uid()) = user_id);
revoke insert, update, delete on public.user_acquisition_profiles from anon, authenticated;
grant select on public.user_acquisition_profiles to authenticated;

create or replace function public.track_growth_event(
  p_event_name text,
  p_source text default null,
  p_metadata jsonb default '{}'::jsonb
) returns void
language plpgsql security definer set search_path to 'public','pg_temp'
as $$
declare
  v_uid uuid := auth.uid();
  v_event text := lower(trim(coalesce(p_event_name,'')));
  v_source text := left(coalesce(nullif(trim(coalesce(p_source,'')),''),'organic'),64);
  v_campaign text := left(nullif(trim(coalesce(p_metadata->>'campaign','')), ''),100);
  v_referral text := upper(left(nullif(trim(coalesce(p_metadata->>'referral_code','')), ''),32));
begin
  if v_uid is null then raise exception 'Authentication required' using errcode='42501'; end if;
  if v_event='' or length(v_event)>64 then raise exception 'Invalid event name' using errcode='22023'; end if;
  insert into public.growth_events(user_id,event_name,source,metadata)
    values(v_uid,v_event,v_source,coalesce(p_metadata,'{}'::jsonb));
  insert into public.user_acquisition_profiles(user_id,first_source,first_campaign,referral_code,first_seen_at,last_seen_at,updated_at)
    values(v_uid,case when v_event='referral_redeemed' then 'referral' else v_source end,v_campaign,v_referral,now(),now(),now())
  on conflict(user_id) do update set
    last_seen_at=now(), updated_at=now(),
    first_source=case when v_event='referral_redeemed' then 'referral' else public.user_acquisition_profiles.first_source end,
    referral_code=coalesce(v_referral,public.user_acquisition_profiles.referral_code),
    first_campaign=coalesce(public.user_acquisition_profiles.first_campaign,v_campaign);
end;
$$;
grant execute on function public.track_growth_event(text,text,jsonb) to authenticated;

create or replace function public.get_my_referral_dashboard() returns jsonb
language plpgsql security definer set search_path to 'public','pg_temp'
as $$
declare
  v_uid uuid := auth.uid(); v_code text; v_count integer; v_xp integer;
  v_shares integer; v_copies integer; v_conversion numeric;
begin
  if v_uid is null then raise exception 'Authentication required' using errcode='42501'; end if;
  insert into public.user_referral_codes(user_id,code)
    values(v_uid,'FX'||upper(substr(replace(v_uid::text,'-',''),1,10))) on conflict(user_id) do nothing;
  select code into v_code from public.user_referral_codes where user_id=v_uid;
  select count(*),coalesce(sum(referrer_xp_awarded),0) into v_count,v_xp from public.referral_redemptions where referrer_user_id=v_uid;
  select count(*) into v_shares from public.growth_events where user_id=v_uid and event_name='referral_share_clicked';
  select count(*) into v_copies from public.growth_events where user_id=v_uid and event_name in('referral_message_copied','referral_code_copied');
  v_conversion := case when v_shares>0 then round((v_count::numeric/v_shares::numeric)*100,1) else 0 end;
  return jsonb_build_object('code',v_code,'successful_referrals',v_count,'earned_xp',v_xp,
    'share_attempts',v_shares,'copy_attempts',v_copies,'conversion_rate_percent',v_conversion,
    'reward_referrer_xp',100,'reward_friend_xp',50);
end;
$$;
grant execute on function public.get_my_referral_dashboard() to authenticated;

create or replace function public.get_my_share_stats() returns jsonb
language sql stable security definer set search_path to 'public','pg_temp'
as $$
select jsonb_build_object(
  'streak_days',coalesce(uhs.streak_days,0), 'xp_earned',coalesce(uhs.xp_earned,0),
  'daily_goal_minutes',coalesce(uhs.daily_goal_progress_minutes,0), 'current_week',coalesce(uhs.current_week,1),
  'cefr_level',coalesce(uhs.current_cefr_level,'A1'), 'weekly_mastery_streak',coalesce(uhs.weekly_mastery_streak,0),
  'total_active_days',coalesce(uhs.total_active_days,0),
  'successful_referrals',coalesce((select count(*) from public.referral_redemptions rr where rr.referrer_user_id=auth.uid()),0),
  'unlocked_achievements',
    (case when coalesce(uhs.streak_days,0)>=7 then 1 else 0 end)+
    (case when coalesce(uhs.streak_days,0)>=30 then 1 else 0 end)+
    (case when coalesce(uhs.xp_earned,0)>=1000 then 1 else 0 end)
) from public.user_home_stats uhs where uhs.user_id=auth.uid();
$$;
grant execute on function public.get_my_share_stats() to authenticated;

create or replace view public.growth_kpis_daily as
with activity as (
 select activity_date day,count(distinct user_id)::integer dau,coalesce(sum(minutes),0)::bigint learning_minutes,coalesce(sum(xp),0)::bigint xp_earned
 from public.user_daily_activity group by activity_date
), events as (
 select (timezone('Asia/Kolkata',created_at))::date day,
 count(*) filter(where event_name='referral_share_clicked')::integer referral_shares,
 count(*) filter(where event_name='referral_redeemed')::integer referral_redeems,
 count(*) filter(where event_name='share_card_shared')::integer share_card_shares,
 count(*) filter(where event_name='app_open')::integer app_opens
 from public.growth_events group by 1
)
select coalesce(a.day,e.day) day,coalesce(a.dau,0) dau,coalesce(a.learning_minutes,0) learning_minutes,
 coalesce(a.xp_earned,0) xp_earned,coalesce(e.referral_shares,0) referral_shares,
 coalesce(e.referral_redeems,0) referral_redeems,coalesce(e.share_card_shares,0) share_card_shares,
 coalesce(e.app_opens,0) app_opens from activity a full join events e using(day);

create or replace view public.growth_acquisition_sources as
select first_source,coalesce(first_campaign,'') campaign,count(*)::integer users
from public.user_acquisition_profiles group by first_source,coalesce(first_campaign,'');

create or replace view public.growth_retention_cohorts as
with firsts as (
 select user_id,min(activity_date) cohort_date from public.user_daily_activity group by user_id
), joined as (
 select f.user_id,f.cohort_date,a.activity_date,(a.activity_date-f.cohort_date) day_offset
 from firsts f join public.user_daily_activity a on a.user_id=f.user_id
)
select cohort_date,count(distinct user_id)::integer cohort_users,
 count(distinct user_id) filter(where day_offset=1)::integer d1_users,
 count(distinct user_id) filter(where day_offset=7)::integer d7_users,
 count(distinct user_id) filter(where day_offset=30)::integer d30_users,
 round(100.0*count(distinct user_id) filter(where day_offset=1)/nullif(count(distinct user_id),0),1) d1_retention_percent,
 round(100.0*count(distinct user_id) filter(where day_offset=7)/nullif(count(distinct user_id),0),1) d7_retention_percent,
 round(100.0*count(distinct user_id) filter(where day_offset=30)/nullif(count(distinct user_id),0),1) d30_retention_percent
from joined group by cohort_date;

revoke all on public.growth_kpis_daily from anon,authenticated;
revoke all on public.growth_acquisition_sources from anon,authenticated;
revoke all on public.growth_retention_cohorts from anon,authenticated;
