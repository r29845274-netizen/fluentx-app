# Incident Runbook

1. Confirm alert and impact with health checks and Supabase/GitHub status.
2. Classify severity: auth outage, database outage, AI/provider degradation, payments, or client crash spike.
3. Enable maintenance mode if continued usage can harm users/data.
4. Preserve logs and timestamps; never paste secrets into tickets.
5. Roll back app/config/migration using the rollback runbook if the latest change caused impact.
6. Communicate a concise status update and expected next checkpoint.
7. After recovery, document root cause, impact window, corrective action and prevention.