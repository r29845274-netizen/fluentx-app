import { createClient } from 'jsr:@supabase/supabase-js@2';

const SUPABASE_URL = Deno.env.get('SUPABASE_URL');
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
const REVENUECAT_SECRET_API_KEY = Deno.env.get('REVENUECAT_SECRET_API_KEY');

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

function tierFromProduct(productIdentifier: string | null): 'free' | 'monthly' | 'annual' {
  const product = (productIdentifier ?? '').toLowerCase();
  if (product.includes('annual') || product.includes('yearly')) return 'annual';
  if (product.includes('monthly') || product.includes('month')) return 'monthly';
  return product ? 'monthly' : 'free';
}

Deno.serve(async (req: Request) => {
  try {
    if (req.method !== 'POST') return json({ error: 'Method not allowed' }, 405);
    if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) return json({ error: 'Server configuration error' }, 500);
    if (!REVENUECAT_SECRET_API_KEY) return json({ error: 'Subscription verifier is not configured' }, 503);

    const authHeader = req.headers.get('Authorization');
    if (!authHeader?.startsWith('Bearer ')) return json({ error: 'Unauthorized' }, 401);

    const admin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
      auth: { persistSession: false, autoRefreshToken: false },
    });
    const { data: authData, error: authError } = await admin.auth.getUser(authHeader.slice(7));
    const user = authData.user;
    if (authError || !user) return json({ error: 'Unauthorized' }, 401);

    const response = await fetch(`https://api.revenuecat.com/v1/subscribers/${encodeURIComponent(user.id)}`, {
      headers: {
        Authorization: `Bearer ${REVENUECAT_SECRET_API_KEY}`,
        Accept: 'application/json',
      },
    });
    if (!response.ok) {
      console.error('RevenueCat verification failed', response.status);
      return json({ error: 'Could not verify subscription' }, 502);
    }

    const payload = await response.json();
    const entitlement = payload?.subscriber?.entitlements?.premium ?? null;
    const productIdentifier = typeof entitlement?.product_identifier === 'string'
      ? entitlement.product_identifier
      : null;
    const expiresDate = typeof entitlement?.expires_date === 'string' ? entitlement.expires_date : null;
    const expiresAt = expiresDate ? new Date(expiresDate) : null;
    const active = Boolean(entitlement) && (!expiresAt || expiresAt.getTime() > Date.now());
    const tier = active ? tierFromProduct(productIdentifier) : 'free';

    const { error: saveError } = await admin.from('user_subscription_access').upsert({
      user_id: user.id,
      tier,
      entitlement_active: active,
      product_identifier: productIdentifier,
      expires_at: expiresAt?.toISOString() ?? null,
      verified_at: new Date().toISOString(),
      source: 'revenuecat_v1',
      updated_at: new Date().toISOString(),
    }, { onConflict: 'user_id' });
    if (saveError) {
      console.error('Could not persist verified subscription', saveError.message);
      return json({ error: 'Could not save subscription status' }, 500);
    }

    return json({ tier, entitlement_active: active, product_identifier: productIdentifier, expires_at: expiresAt?.toISOString() ?? null });
  } catch (error) {
    console.error('sync-subscription-access error', error instanceof Error ? error.message : String(error));
    return json({ error: 'Subscription verification failed' }, 502);
  }
});