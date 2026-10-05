# FluentX Architecture

Flutter mobile client -> Supabase Auth/Postgres/Edge Functions. Firebase handles Crashlytics/Analytics/Messaging. RevenueCat handles subscription entitlements. AI practice/writing scoring use server-side Edge Functions so private provider credentials never ship in the client.

Security boundaries: Supabase RLS for row ownership, Edge Functions for privileged operations, admin MFA/roles for internal tools, server-owned AI scoring, device/session registry, audit logging, rate limits and idempotency.