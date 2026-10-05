# FluentX Service Status

**Production:** Operational  
**Auth/Database:** Supabase production project `rdrvqszejpupaqeitmmu`  
**Synthetic monitoring:** every 15 minutes via GitHub Actions  
**Health endpoint:** `/functions/v1/health`  
**Live endpoint:** `/functions/v1/health/live`

## Current verification evidence

- Prelaunch gate: PASS
- Uptime monitor: PASS
- Health load test: PASS
- 500 requests at concurrency 25: 500 successful, 0% errors
- p50: 402.04 ms
- p95: 972.74 ms
- p99: 1124.49 ms
- max: 1450.09 ms

Incidents are handled using `docs/runbooks/incident.md`.
