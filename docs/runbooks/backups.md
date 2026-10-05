# Backup / Restore Runbook

Production data is hosted in Supabase. Backup availability depends on the active Supabase plan. On Free plan, downloadable managed backups/PITR are not guaranteed.

For a production launch that requires tested restore evidence:
1. Use a paid staging branch/project approved by the owner.
2. Export schema and representative non-sensitive test data.
3. Restore into staging.
4. Run migrations, RLS tests, health checks and core-flow tests.
5. Record restore duration and RPO/RTO.
Never perform a destructive restore drill against production.