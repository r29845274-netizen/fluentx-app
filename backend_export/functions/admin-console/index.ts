import { createClient } from 'jsr:@supabase/supabase-js@2';

const SUPABASE_URL = Deno.env.get('SUPABASE_URL');
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

type AdminRole = 'owner' | 'admin' | 'support';

type AdminRow = {
  user_id: string;
  role: AdminRole;
  is_active: boolean;
};

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff',
      'Referrer-Policy': 'no-referrer',
    },
  });
}

function safeInt(value: unknown, fallback: number, min: number, max: number) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.max(min, Math.min(max, Math.trunc(parsed)));
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const part = token.split('.')[1];
    if (!part) return null;
    const normalized = part.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
    return JSON.parse(atob(padded));
  } catch {
    return null;
  }
}

async function audit(
  admin: ReturnType<typeof createClient>,
  adminUserId: string,
  action: string,
  targetUserId: string | null,
  reason: string | null,
  metadata: Record<string, unknown> = {},
) {
  const { error } = await admin.from('admin_audit_log').insert({
    admin_user_id: adminUserId,
    action,
    target_user_id: targetUserId,
    reason,
    metadata,
  });
  if (error) console.error('admin audit log failed', error.message);
}

Deno.serve(async (req: Request) => {
  if (req.method !== 'POST') return json({ error: 'Method not allowed' }, 405);
  if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
    return json({ error: 'Server configuration error' }, 500);
  }

  const authHeader = req.headers.get('Authorization');
  if (!authHeader?.startsWith('Bearer ')) return json({ error: 'Unauthorized' }, 401);
  const token = authHeader.slice('Bearer '.length);

  const admin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  const { data: userResult, error: userError } = await admin.auth.getUser(token);
  const caller = userResult.user;
  if (userError || !caller) return json({ error: 'Unauthorized' }, 401);

  const { data: adminRow, error: adminError } = await admin
    .from('admin_users')
    .select('user_id, role, is_active')
    .eq('user_id', caller.id)
    .eq('is_active', true)
    .maybeSingle();

  if (adminError) return json({ error: 'Authorization check failed' }, 500);
  if (!adminRow) return json({ error: 'Admin access denied', code: 'NOT_ADMIN' }, 403);

  const adminUser = adminRow as AdminRow;
  const jwt = decodeJwtPayload(token);
  const aal = typeof jwt?.aal === 'string' ? jwt.aal : null;

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return json({ error: 'Invalid JSON' }, 400);
  }
  const action = typeof body.action === 'string' ? body.action : 'status';

  // Status is intentionally available at aal1 so the app can tell a real admin
  // that a second factor must be completed. No user data is returned here.
  if (action === 'status') {
    return json({
      is_admin: true,
      role: adminUser.role,
      mfa_verified: aal === 'aal2',
      requires_mfa: aal !== 'aal2',
    });
  }

  if (aal !== 'aal2') {
    return json({ error: 'Admin MFA verification required', code: 'MFA_REQUIRED' }, 403);
  }

  if (action === 'overview') {
    const [usersResult, sessionsResult, writingResult] = await Promise.all([
      admin.auth.admin.listUsers({ page: 1, perPage: 1 }),
      admin.from('ai_practice_sessions').select('id', { count: 'exact', head: true }),
      admin.from('writing_submissions').select('id', { count: 'exact', head: true }),
    ]);
    if (usersResult.error) return json({ error: 'Could not load users' }, 500);
    await audit(admin, caller.id, 'overview', null, null);
    return json({
      total_users: usersResult.data.total ?? 0,
      ai_sessions: sessionsResult.count ?? 0,
      writing_submissions: writingResult.count ?? 0,
    });
  }

  if (action === 'list_users') {
    const page = safeInt(body.page, 1, 1, 100000);
    const perPage = safeInt(body.per_page, 25, 1, 50);
    const search = typeof body.search === 'string' ? body.search.trim().toLowerCase().slice(0, 200) : '';

    const { data, error } = await admin.auth.admin.listUsers({ page, perPage: search ? 1000 : perPage });
    if (error) return json({ error: 'Could not load users' }, 500);

    let users = data.users;
    if (search) {
      users = users.filter((u) => {
        const email = (u.email ?? '').toLowerCase();
        const name = String(u.user_metadata?.full_name ?? u.user_metadata?.name ?? '').toLowerCase();
        return email.includes(search) || name.includes(search) || u.id.toLowerCase().includes(search);
      }).slice(0, perPage);
    }

    const userIds = users.map((u) => u.id);
    const statsMap = new Map<string, Record<string, unknown>>();
    if (userIds.length > 0) {
      const { data: stats } = await admin
        .from('user_home_stats')
        .select('user_id, streak_days, xp_earned, daily_goal_progress_minutes, updated_at')
        .in('user_id', userIds);
      for (const row of stats ?? []) statsMap.set(row.user_id, row);
    }

    await audit(admin, caller.id, 'list_users', null, search || null, { page, per_page: perPage });
    return json({
      page,
      per_page: perPage,
      total: data.total ?? users.length,
      users: users.map((u) => ({
        id: u.id,
        email: u.email ?? null,
        full_name: u.user_metadata?.full_name ?? u.user_metadata?.name ?? null,
        created_at: u.created_at,
        last_sign_in_at: u.last_sign_in_at ?? null,
        email_confirmed_at: u.email_confirmed_at ?? null,
        is_anonymous: u.is_anonymous ?? false,
        stats: statsMap.get(u.id) ?? null,
      })),
    });
  }

  if (action === 'user_detail') {
    const targetUserId = typeof body.user_id === 'string' ? body.user_id : '';
    if (!targetUserId) return json({ error: 'user_id is required' }, 400);

    const { data: targetResult, error: targetError } = await admin.auth.admin.getUserById(targetUserId);
    const target = targetResult.user;
    if (targetError || !target) return json({ error: 'User not found' }, 404);

    const [home, vocab, grammar, listening, aiSessions, writing] = await Promise.all([
      admin.from('user_home_stats').select('streak_days, xp_earned, daily_goal_target_minutes, daily_goal_progress_minutes, updated_at').eq('user_id', targetUserId).maybeSingle(),
      admin.from('user_vocabulary_progress').select('word_id', { count: 'exact', head: true }).eq('user_id', targetUserId),
      admin.from('user_grammar_mistakes').select('mistake_count').eq('user_id', targetUserId),
      admin.from('user_listening_progress').select('score').eq('user_id', targetUserId),
      admin.from('ai_practice_sessions').select('accuracy_score, started_at, ended_at').eq('user_id', targetUserId).order('started_at', { ascending: false }).limit(20),
      admin.from('writing_submissions').select('grammar_score, clarity_score, structure_score, tone_score, scored_at').eq('user_id', targetUserId).order('created_at', { ascending: false }).limit(20),
    ]);

    const grammarMistakes = (grammar.data ?? []).reduce((sum, r) => sum + Number(r.mistake_count ?? 0), 0);
    const listeningScores = (listening.data ?? []).map((r) => Number(r.score)).filter(Number.isFinite);
    const avgListening = listeningScores.length
      ? listeningScores.reduce((a, b) => a + b, 0) / listeningScores.length
      : null;

    await audit(admin, caller.id, 'user_detail', targetUserId, null);
    return json({
      user: {
        id: target.id,
        email: target.email ?? null,
        full_name: target.user_metadata?.full_name ?? target.user_metadata?.name ?? null,
        created_at: target.created_at,
        last_sign_in_at: target.last_sign_in_at ?? null,
        email_confirmed_at: target.email_confirmed_at ?? null,
      },
      learning: {
        home: home.data ?? null,
        vocabulary_reviews: vocab.count ?? 0,
        grammar_mistakes: grammarMistakes,
        average_listening_score: avgListening,
        recent_ai_sessions: aiSessions.data ?? [],
        recent_writing_scores: writing.data ?? [],
      },
    });
  }

  if (action === 'user_private_content') {
    if (adminUser.role === 'support') return json({ error: 'Insufficient admin role' }, 403);
    const targetUserId = typeof body.user_id === 'string' ? body.user_id : '';
    const reason = typeof body.reason === 'string' ? body.reason.trim().slice(0, 500) : '';
    if (!targetUserId) return json({ error: 'user_id is required' }, 400);
    if (reason.length < 10) return json({ error: 'A meaningful access reason is required' }, 400);

    const [writing, sessions] = await Promise.all([
      admin
        .from('writing_submissions')
        .select('id, content, grammar_score, clarity_score, structure_score, tone_score, ai_feedback, created_at, scored_at')
        .eq('user_id', targetUserId)
        .order('created_at', { ascending: false })
        .limit(20),
      admin
        .from('ai_practice_sessions')
        .select('id, transcript, accuracy_score, fluency_notes, corrected_sentences, started_at, ended_at')
        .eq('user_id', targetUserId)
        .order('started_at', { ascending: false })
        .limit(20),
    ]);

    await audit(admin, caller.id, 'user_private_content', targetUserId, reason, {
      writing_rows: writing.data?.length ?? 0,
      session_rows: sessions.data?.length ?? 0,
    });
    return json({ writing: writing.data ?? [], ai_sessions: sessions.data ?? [] });
  }

  if (action === 'audit_log') {
    if (adminUser.role !== 'owner') return json({ error: 'Owner role required' }, 403);
    const limit = safeInt(body.limit, 100, 1, 200);
    const { data, error } = await admin
      .from('admin_audit_log')
      .select('id, admin_user_id, action, target_user_id, reason, metadata, created_at')
      .order('created_at', { ascending: false })
      .limit(limit);
    if (error) return json({ error: 'Could not load audit log' }, 500);
    await audit(admin, caller.id, 'audit_log', null, null, { limit });
    return json({ events: data ?? [] });
  }

  return json({ error: 'Unknown action' }, 400);
});
