// FluentX — score-writing Edge Function (Gemini)
//
// Server-side only. Required custom secret: GEMINI_API_KEY.
// Supabase provides SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to hosted functions.

import { createClient } from 'jsr:@supabase/supabase-js@2';

const GEMINI_API_KEY = Deno.env.get('GEMINI_API_KEY');
const SUPABASE_URL = Deno.env.get('SUPABASE_URL');
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
const GEMINI_MODEL = 'gemini-3.6-flash';

type ScorePayload = {
  grammar_score: number;
  clarity_score: number;
  structure_score: number;
  tone_score: number;
  feedback: string;
};

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function extractText(payload: any): string {
  const parts = payload?.candidates?.[0]?.content?.parts;
  if (!Array.isArray(parts)) return '';
  return parts.map((part: any) => typeof part?.text === 'string' ? part.text : '').join('').trim();
}

function clampScore(value: unknown): number {
  const n = Number(value);
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, Math.min(100, Math.round(n)));
}

async function callGemini(systemPrompt: string, userText: string): Promise<ScorePayload> {
  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-goog-api-key': GEMINI_API_KEY!,
      },
      body: JSON.stringify({
        systemInstruction: { parts: [{ text: systemPrompt }] },
        contents: [{ role: 'user', parts: [{ text: userText }] }],
        generationConfig: {
          temperature: 0.25,
          responseFormat: {
            text: {
              mimeType: 'application/json',
              schema: {
                type: 'object',
                properties: {
                  grammar_score: { type: 'integer', minimum: 0, maximum: 100 },
                  clarity_score: { type: 'integer', minimum: 0, maximum: 100 },
                  structure_score: { type: 'integer', minimum: 0, maximum: 100 },
                  tone_score: { type: 'integer', minimum: 0, maximum: 100 },
                  feedback: { type: 'string' },
                },
                required: ['grammar_score', 'clarity_score', 'structure_score', 'tone_score', 'feedback'],
              },
            },
          },
        },
      }),
    },
  );

  if (!response.ok) {
    const errorText = await response.text();
    console.error(`Gemini score-writing error ${response.status}:`, errorText);
    if (response.status === 429) throw new Error('GEMINI_RATE_LIMIT');
    if (response.status === 401 || response.status === 403) throw new Error('GEMINI_AUTH');
    throw new Error('GEMINI_REQUEST');
  }

  const payload = await response.json();
  const text = extractText(payload);
  if (!text) throw new Error('GEMINI_EMPTY');

  const parsed = JSON.parse(text) as Partial<ScorePayload>;
  return {
    grammar_score: clampScore(parsed.grammar_score),
    clarity_score: clampScore(parsed.clarity_score),
    structure_score: clampScore(parsed.structure_score),
    tone_score: clampScore(parsed.tone_score),
    feedback: String(parsed.feedback ?? '').trim(),
  };
}

Deno.serve(async (req: Request) => {
  try {
    if (req.method !== 'POST') return json({ error: 'Method not allowed' }, 405);
    if (!GEMINI_API_KEY || !SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
      return json({ error: 'Server misconfigured: missing required secrets.' }, 500);
    }

    const body = await req.json();
    const submissionId = body?.submission_id;
    if (!submissionId) return json({ error: 'submission_id is required' }, 400);

    const authHeader = req.headers.get('Authorization');
    if (!authHeader?.startsWith('Bearer ')) return json({ error: 'Unauthorized' }, 401);

    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);
    const token = authHeader.slice('Bearer '.length);
    const { data: authData, error: authError } = await supabase.auth.getUser(token);
    const user = authData.user;
    if (authError || !user) return json({ error: 'Unauthorized' }, 401);

    const { data: submission, error: fetchError } = await supabase
      .from('writing_submissions')
      .select('id, content, prompt_id, writing_prompts(title, category, instructions)')
      .eq('id', submissionId)
      .eq('user_id', user.id)
      .single();

    if (fetchError || !submission) return json({ error: 'Submission not found' }, 404);

    const prompt = submission.writing_prompts as {
      title: string;
      category: string;
      instructions: string;
    };

    const systemPrompt = `You are the FluentX English writing coach for Indian learners.
Evaluate the user's ${prompt.category} writing for the task "${prompt.title}".
Task instructions: ${prompt.instructions}
Score grammar, clarity, structure, and tone from 0 to 100.
Give 2-3 concise, encouraging, actionable sentences. Point out the most useful improvement first.
Do not claim to be a human teacher.`;

    let parsed: ScorePayload;
    try {
      parsed = await callGemini(systemPrompt, String(submission.content ?? ''));
    } catch (error) {
      const code = error instanceof Error ? error.message : 'GEMINI_REQUEST';
      if (code === 'GEMINI_RATE_LIMIT') {
        return json({ error: 'AI feedback limit reached. Please try again shortly.' }, 429);
      }
      if (code === 'GEMINI_AUTH') {
        return json({ error: 'AI provider authentication failed.' }, 502);
      }
      console.error('Gemini scoring failure:', error);
      return json({ error: 'AI scoring failed. Please try again.' }, 502);
    }

    const { data: updated, error: updateError } = await supabase
      .from('writing_submissions')
      .update({
        grammar_score: parsed.grammar_score,
        clarity_score: parsed.clarity_score,
        structure_score: parsed.structure_score,
        tone_score: parsed.tone_score,
        ai_feedback: parsed.feedback,
        scored_at: new Date().toISOString(),
      })
      .eq('id', submissionId)
      .eq('user_id', user.id)
      .select()
      .single();

    if (updateError || !updated) {
      console.error('Score save error:', updateError);
      return json({ error: 'Failed to save scores' }, 500);
    }

    return json(updated, 200);
  } catch (error) {
    console.error('score-writing unexpected error:', error);
    return json({ error: 'Unexpected server error.' }, 500);
  }
});
