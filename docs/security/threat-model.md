# Threat model

Assets: accounts, sessions, learning history, writing/transcripts, payment entitlement state, admin access and AI budget.

Controls:
- Broken object access: RLS + explicit ownership checks.
- Forged assessments: scored fields are server-controlled.
- AI abuse/cost: authenticated ownership checks, request limits, hourly quotas and leases.
- Retry duplication: idempotent reply receipts.
- Admin abuse: allowlist, roles, MFA, audit logs.
- Secret leakage: server secrets stay in server/runtime configuration; client receives publishable keys only.
- Account compromise: Supabase Auth + recovery, session/device registry and revocation.
- Error leakage: user-facing errors are generic; backend detail stays out of UI.