// FluentX — ai-practice-chat Edge Function (Gemini)
//
// Two actions:
//  - { action: 'reply', session_id, user_message }
//  - { action: 'summarize', session_id }
// Required custom secret: GEMINI_API_KEY.

import { createClient } from 'jsr:@supabase/supabase-js@2';

const GEMINI_API_KEY = Deno.env.get('GEMINI_API_KEY');
const SUPABASE_URL = Deno.env.get('SUPABASE_URL');
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
const GEMINI_MODEL = 'gemini-3.6-flash';

type TranscriptTurn = { role: 'user' | 'assistant'; text: string };

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

async function callGemini(params: {
  systemInstruction: string;
  contents: Array<{ role: 'user' | 'model'; parts: Array<{ text: string }> }>;
  schema: Record<string, unknown>;
}) {
  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-goog-api-key': GEMINI_API_KEY!,
      },
      body: JSON.stringify({
        systemInstruction: { parts: [{ text: params.systemInstruction }] },
        contents: params.contents,
        generationConfig: {
          temperature: 0.35,
          responseFormat: {
            text: {
              mimeType: 'application/json',
              schema: params.schema,
            },
          },
        },
      }),
    },
  );

  if (!response.ok) {
    const text = await response.text();
    console.error(`Gemini ai-practice error ${response.status}:`, text);
    if (response.status === 429) throw new Error('GEMINI_RATE_LIMIT');
    if (response.status === 401 || response.status === 403) throw new Error('GEMINI_AUTH');
    throw new Error('GEMINI_REQUEST');
  }

  const payload = await response.json();
  const text = extractText(payload);
  if (!text) throw new Error('GEMINI_EMPTY');
  return JSON.parse(text);
}

Deno.serve(async (req: Request) => {
  try {
    if (req.method !== 'POST') return json({ error: 'Method not allowed' }, 405);
    if (!GEMINI_API_KEY || !SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
      return json({ error: 'Server misconfigured: missing required secrets.' }, 500);
    }

    const body = await req.json();
    const action = body?.action;
    const sessionId = body?.session_id;
    if (!sessionId) return json({ error: 'session_id is required' }, 400);

    const authHeader = req.headers.get('Authorization');
    if (!authHeader?.startsWith('Bearer ')) return json({ error: 'Unauthorized' }, 401);

    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);
    const token = authHeader.slice('Bearer '.length);
    const { data: authData, error: authError } = await supabase.auth.getUser(token);
    const user = authData.user;
    if (authError || !user) return json({ error: 'Unauthorized' }, 401);

    const { data: session, error: sessionError } = await supabase
      .from('ai_practice_sessions')
      .select('id, transcript, ai_practice_scenarios(system_prompt)')
      .eq('id', sessionId)
      .eq('user_id', user.id)
      .single();

    if (sessionError || !session) return json({ error: 'Session not found' }, 404);

    const scenario = session.ai_practice_scenarios as { system_prompt: string };
    const transcript: TranscriptTurn[] = Array.isArray(session.transcript) ? session.transcript : [];

    if (action === 'reply') {
      const userMessage = String(body?.user_message ?? '').trim();
      if (!userMessage) return json({ error: 'user_message is required' }, 400);

      const contents = [
        ...transcript.map((turn) => ({
          role: turn.role === 'assistant' ? 'model' as const : 'user' as const,
          parts: [{ text: turn.text }],
        })),
        { role: 'user' as const, parts: [{ text: userMessage }] },
      ];

      let parsed: any;
      try {
        parsed = await callGemini({
          systemInstruction: `${scenario.system_prompt}\n\nYou are an AI English coach. Keep the roleplay natural and concise. If the user's latest message has a useful grammar or word-choice correction, provide one encouraging correction; otherwise return an empty correction string.`,
          contents,
          schema: {
            type: 'object',
            properties: {
              reply: { type: 'string' },
              correction: { type: 'string' },
            },
            required: ['reply', 'correction'],
          },
        });
      } catch (error) {
        const code = error instanceof Error ? error.message : 'GEMINI_REQUEST';
        if (code === 'GEMINI_RATE_LIMIT') return json({ error: 'AI coach limit reached. Please try again shortly.' }, 429);
        console.error('Gemini reply failure:', error);
        return json({ error: 'The AI coach is unavailable right now.' }, 502);
      }

      const reply = String(parsed?.reply ?? '').trim();
      if (!reply) return json({ error: 'The AI coach returned an empty reply.' }, 502);
      const correctionText = String(parsed?.correction ?? '').trim();

      const updatedTranscript: TranscriptTurn[] = [
        ...transcript,
        { role: 'user', text: userMessage },
        { role: 'assistant', text: reply },
      ];

      const { error: updateError } = await supabase
        .from('ai_practice_sessions')
        .update({ transcript: updatedTranscript })
        .eq('id', sessionId)
        .eq('user_id', user.id);
      if (updateError) console.error('Transcript update error:', updateError);

      return json({ reply, correction: correctionText || null }, 200);
    }

    if (action === 'summarize') {
      const userTurns = transcript.filter((turn) => turn.role === 'user').map((turn) => turn.text);

      let parsed: any;
      try {
        parsed = await callGemini({
          systemInstruction: `You are the FluentX English speaking coach for Indian learners. Evaluate only the learner's transcribed turns. The transcript can support grammar, vocabulary, sentence quality, and text-based fluency observations, but it cannot prove phoneme-level pronunciation. Give an accuracy score from 0 to 100, 2-3 specific encouraging fluency notes, and at most 3 corrected sentences.`,
          contents: [{ role: 'user', parts: [{ text: JSON.stringify(userTurns) }] }],
          schema: {
            type: 'object',
            properties: {
              accuracy_score: { type: 'integer', minimum: 0, maximum: 100 },
              fluency_notes: { type: 'string' },
              corrected_sentences: {
                type: 'array',
                maxItems: 3,
                items: {
                  type: 'object',
                  properties: {
                    original: { type: 'string' },
                    corrected: { type: 'string' },
                  },
                  required: ['original', 'corrected'],
                },
              },
            },
            required: ['accuracy_score', 'fluency_notes', 'corrected_sentences'],
          },
        });
      } catch (error) {
        const code = error instanceof Error ? error.message : 'GEMINI_REQUEST';
        if (code === 'GEMINI_RATE_LIMIT') return json({ error: 'AI coach limit reached. Please try again shortly.' }, 429);
        console.error('Gemini summary failure:', error);
        return json({ error: 'Could not generate your session summary.' }, 502);
      }

      const accuracy = Math.max(0, Math.min(100, Math.round(Number(parsed?.accuracy_score ?? 0))));
      const fluencyNotes = String(parsed?.fluency_notes ?? '').trim();
      const corrected = Array.isArray(parsed?.corrected_sentences) ? parsed.corrected_sentences.slice(0, 3) : [];

      const { data: updated, error: updateError } = await supabase
        .from('ai_practice_sessions')
        .update({
          accuracy_score: accuracy,
          fluency_notes: fluencyNotes,
          corrected_sentences: corrected,
          ended_at: new Date().toISOString(),
        })
        .eq('id', sessionId)
        .eq('user_id', user.id)
        .select()
        .single();

      if (updateError || !updated) {
        console.error('Session summary save error:', updateError);
        return json({ error: 'Could not save your session summary.' }, 500);
      }

      return json({
        accuracy_score: accuracy,
        fluency_notes: fluencyNotes,
        corrected_sentences: corrected,
      }, 200);
    }

    return json({ error: 'Unsupported action' }, 400);
  } catch (error) {
    console.error('ai-practice-chat unexpected error:', error);
    return json({ error: 'Unexpected server error.' }, 500);
  }
});
