-- FluentX — Communication DNA™
--
-- ⚠️ v1 heuristic scoring, documented honestly:
-- - Grammar: derived from `user_grammar_mistakes` volume (fewer
--   mistakes → higher score). Not a true error-rate (we don't yet
--   store total questions answered, only wrong ones) — refine in a
--   later sprint by also tracking attempt counts.
-- - Pronunciation: averages `user_listening_progress.score` (quiz
--   comprehension, a proxy) with `ai_practice_sessions.accuracy_score`
--   (LLM-estimated during conversation) since there's no Azure
--   Pronunciation Assessment integration yet (flagged as a future
--   upgrade in the original product spec).
-- - Fluency: LLM-estimated per AI Practice session.
-- - Vocabulary: % of the vocabulary deck reviewed at least once.
-- - Confidence: normalized AI Practice session frequency, as a proxy
--   for willingness to practice speaking.
-- Weights match the product spec: Fluency 25%, Vocabulary 20%,
-- Grammar 20%, Pronunciation 20%, Confidence 15%.

create or replace function public.get_communication_dna(p_user_id uuid)
returns table (
  fluency_score integer,
  vocabulary_score integer,
  grammar_score integer,
  pronunciation_score integer,
  confidence_score integer,
  overall_score integer
)
language plpgsql
stable
as $$
declare
  v_fluency numeric := 0;
  v_vocabulary numeric := 0;
  v_grammar numeric := 0;
  v_pronunciation numeric := 0;
  v_confidence numeric := 0;
  v_total_words integer;
  v_reviewed_words integer;
  v_mistake_total integer;
  v_listening_avg numeric;
  v_ai_avg numeric;
  v_session_count integer;
begin
  select count(*) into v_total_words from public.vocabulary_words;
  select count(*) into v_reviewed_words
    from public.user_vocabulary_progress where user_id = p_user_id;
  v_vocabulary := case
    when v_total_words = 0 then 0
    else least(100, (v_reviewed_words::numeric / v_total_words) * 100)
  end;

  select coalesce(sum(mistake_count), 0) into v_mistake_total
    from public.user_grammar_mistakes where user_id = p_user_id;
  v_grammar := greatest(30, 100 - (v_mistake_total * 4));

  select avg(score) into v_listening_avg
    from public.user_listening_progress where user_id = p_user_id;

  select avg(accuracy_score), count(*) into v_ai_avg, v_session_count
    from public.ai_practice_sessions
    where user_id = p_user_id and accuracy_score is not null;

  v_pronunciation := (coalesce(v_listening_avg, 0) + coalesce(v_ai_avg, 0))
    / greatest(1, (case when v_listening_avg is null then 0 else 1 end
                 + case when v_ai_avg is null then 0 else 1 end));

  v_fluency := coalesce(v_ai_avg, 0);
  v_confidence := least(100, coalesce(v_session_count, 0) * 10);

  return query select
    round(v_fluency)::integer,
    round(v_vocabulary)::integer,
    round(v_grammar)::integer,
    round(v_pronunciation)::integer,
    round(v_confidence)::integer,
    round(
      v_fluency * 0.25 + v_vocabulary * 0.20 + v_grammar * 0.20
      + v_pronunciation * 0.20 + v_confidence * 0.15
    )::integer;
end;
$$;

grant execute on function public.get_communication_dna(uuid) to authenticated;
