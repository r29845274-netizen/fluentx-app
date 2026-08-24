import { createClient } from 'jsr:@supabase/supabase-js@2';

const SUPABASE_URL = Deno.env.get('SUPABASE_URL');
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff',
    },
  });
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

Deno.serve(async (req: Request) => {
  try {
    if (req.method !== 'POST') return json({ error: 'Method not allowed' }, 405);
    if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) return json({ error: 'Server configuration error' }, 500);

    const authHeader = req.headers.get('Authorization');
    if (!authHeader?.startsWith('Bearer ')) return json({ error: 'Unauthorized' }, 401);
    const token = authHeader.slice(7);

    const admin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
      auth: { persistSession: false, autoRefreshToken: false },
    });
    const { data: authData, error: authError } = await admin.auth.getUser(token);
    const user = authData.user;
    if (authError || !user) return json({ error: 'Unauthorized' }, 401);

    const { data: adminRow, error: adminError } = await admin
      .from('admin_users')
      .select('role,is_active')
      .eq('user_id', user.id)
      .eq('is_active', true)
      .maybeSingle();
    if (adminError) return json({ error: 'Authorization check failed' }, 500);
    if (!adminRow) return json({ error: 'Admin access denied' }, 403);

    const jwt = decodeJwtPayload(token);
    if (jwt?.aal !== 'aal2') return json({ error: 'Admin MFA verification required', code: 'MFA_REQUIRED' }, 403);

    let body: any = {};
    try { body = await req.json(); } catch {}
    const days = Math.max(7, Math.min(90, Math.trunc(Number(body?.days ?? 30))));
    const since = new Date(Date.now() - (days - 1) * 86400000).toISOString().slice(0, 10);

    const [daily, sources, cohorts, referrals, activeUsers] = await Promise.all([
      admin.from('growth_kpis_daily').select('*').gte('day', since).order('day', { ascending: true }),
      admin.from('growth_acquisition_sources').select('*').order('users', { ascending: false }).limit(20),
      admin.from('growth_retention_cohorts').select('*').order('cohort_date', { ascending: false }).limit(30),
      admin.from('referral_redemptions').select('referred_user_id', { count: 'exact', head: true }),
      admin.from('user_daily_activity').select('user_id').gte('activity_date', since),
    ]);

    const uniqueActive = new Set((activeUsers.data ?? []).map((r: any) => r.user_id)).size;
    const dailyRows = daily.data ?? [];
    const totalShares = dailyRows.reduce((s: number, r: any) => s + Number(r.referral_shares ?? 0), 0);
    const totalRedeems = dailyRows.reduce((s: number, r: any) => s + Number(r.referral_redeems ?? 0), 0);
    const shareCardShares = dailyRows.reduce((s: number, r: any) => s + Number(r.share_card_shares ?? 0), 0);
    const learningMinutes = dailyRows.reduce((s: number, r: any) => s + Number(r.learning_minutes ?? 0), 0);
    const referralConversion = totalShares > 0 ? Math.round((totalRedeems / totalShares) * 1000) / 10 : 0;

    return json({
      window_days: days,
      active_users: uniqueActive,
      learning_minutes: learningMinutes,
      referral_shares: totalShares,
      referral_redeems: totalRedeems,
      referral_conversion_percent: referralConversion,
      share_card_shares: shareCardShares,
      total_referrals_all_time: referrals.count ?? 0,
      daily: dailyRows,
      acquisition_sources: sources.data ?? [],
      retention_cohorts: cohorts.data ?? [],
    });
  } catch (error) {
    console.error('growth-admin-analytics', error instanceof Error ? error.message : String(error));
    return json({ error: 'Growth analytics failed' }, 500);
  }
});