# Monitoring

Monitor app startup failures, auth errors, Edge Function 4xx/5xx, AI 429/502 rate, Postgres errors, purchase failures, crash-free users and support backlog.

Client crash sink: Firebase Crashlytics.
Backend logs: Supabase function/database logs.
Synthetic checks: GitHub Actions scheduled health monitor against /functions/v1/health/live and /functions/v1/health.

Alerts should be actionable and link to docs/runbooks/incident.md.