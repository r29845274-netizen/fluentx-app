// FluentX — score-placement-speaking Edge Function (Gemini)
// Scores placement-test speaking transcripts and stores the result server-side.
// Required custom secret: GEMINI_API_KEY.

import { createClient } from 'jsr:@supabase/supabase-js@2';

const GEMINI_API_KEY = Deno.env.get('GEMINI_API_KEY');
const SUPABASE_URL = Deno.env.get('SUPABASE_URL');
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
const GEMINI_MODEL = 'gemini-3.6-flash';

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });
}

function extractText(payload: any): string {
  const parts = payload?.candidates?.[0]?.content?.parts;
  if (!Array.isArray(parts)) return '';
  return parts.map((part: any) => typeof part?.text === 'string' ? part.text : '').join('').trim();
}

Deno.serve(async (req: Request) => {
  try {
    if (req.method !== 'POST') return json({ error: 'Method not allowed' }, 405);
    if (!GEMINI_API_KEY || !SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
      return json({ error: 'Server misconfigured: missing required secrets.' }, 500);
    }

    const authHeader = req.headers.get('Authorization');
    if (!authHeader?.startsWith('Bearer ')) return json({ error: 'Unauthorized' }, 401);

    const body = await req.json();
    const attemptId = body?.attempt_id;
    const questionId = body?.question_id;
    const spokenText = String(body?.spoken_text ?? '').trim();
    if (!attemptId || !questionId || !spokenText) return json({ error: 'attempt_id, question_id and spoken_text are required' }, 400);

    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);
    const token = authHeader.slice('Bearer '.length);
    const { data: authData, error: authError } = await supabase.auth.getUser(token);
    const user = authData.user;
    if (authError || !user) return json({ error: 'Unauthorized' }, 401);

    const { data: question, error: questionError } = await supabase
      .from('placement_questions')
      .select('id, prompt, cefr_level, difficulty_rank, skill')
      .eq('id', questionId)
      .eq('question_type', 'speaking')
      .single();
    if (questionError || !question) return json({ error: 'Placement question not found' }, 404);

    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-goog-api-key': GEMINI_API_KEY },
        body: JSON.stringify({
          contents: [{
            role: 'user',
            parts: [{ text: `Placement speaking prompt: ${question.prompt}\nTarget level: ${question.cefr_level}\nLearner transcript: ${spokenText}\n\nScore the transcript from 0-100 for grammatical control, vocabulary range, relevance, and sentence fluency. Do not pretend to measure phoneme-level pronunciation because only a transcript is available.` }],
          }],
          generationConfig: {
            temperature: 0.2,
            responseFormat: {
              text: {
                mimeType: 'application/json',
                schema: {
                  type: 'object',
                  properties: {
                    score: { type: 'integer', minimum: 0, maximum: 100 },
                    feedback: { type: 'string' },
                  },
                  required: ['score', 'feedback'],
                },
              },
            },
          },
        }),
      },
    );

    if (!response.ok) {
      console.error(`Gemini placement error ${response.status}:`, await response.text());
      return json({ error: 'AI speaking score failed.' }, response.status === 429 ? 429 : 502);
    }

    const payload = await response.json();
    const parsed = JSON.parse(extractText(payload));
    const score = Math.max(0, Math.min(100, Math.round(Number(parsed?.score ?? 0))));
    const feedback = String(parsed?.feedback ?? '').trim();

    const { error: saveError } = await supabase
      .from('placement_answers')
      .upsert({
        attempt_id: attemptId,
        user_id: user.id,
        question_id: questionId,
        spoken_text: spokenText,
        speaking_score: score,
        speaking_feedback: feedback,
      }, { onConflict: 'attempt_id,question_id' });

    if (saveError) {
      console.error('Placement speaking save error:', saveError);
      return json({ error: 'Could not save speaking score.' }, 500);
    }

    return json({ score, feedback }, 200);
  } catch (error) {
    console.error('score-placement-speaking unexpected error:', error);
    return json({ error: 'Unexpected server error.' }, 500);
  }
});
