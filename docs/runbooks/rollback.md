# Rollback Runbook

App: redeploy/reinstall the last known-good GitHub Actions artifact.
Edge Functions: redeploy the previous known-good function version/source.
Database: prefer forward-fix migrations. Never drop/undo production data destructively without a reviewed recovery plan.
Feature incidents: disable AI/premium/announcements or enable maintenance mode from app_config.
Validate health, auth and support flows after rollback.