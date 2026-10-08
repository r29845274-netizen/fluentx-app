# FluentX security closure — 2026-10-08

## Changes deployed and verified
- Production and staging `admin-bootstrap` (old key-based Edge Function) replaced with 404 handler. Modern `owner-bootstrap` unchanged.
- Applied `0033_retire_legacy_admin_claim_paths` migration to production and staging.
- Legacy bootstrap keys have no unused records; active legacy invites are zero in both environments.
- Production legacy `claim_first_owner(text)` and `claim_admin_invite()` functions return denied and are not executable by `anon` or `authenticated`.
- `admin-extended` invitation list/save/revoke actions now respond 404; `role-admin` remains the designated owner-only role mutation function.
- Corresponding migration and deployed `admin-extended` source committed to GitHub.

## Verified outstanding / not launch-approved
- Production `user_roles` owner count = 0. Actual owner enrollment requires verified mailbox and MFA enrollment by account holder; no automated claim attempted.
- External Google/Apple/Firebase/RevenueCat/OpenAI production integrations and physical-device end-to-end tests have not been verified here.
- Supabase advisor reports authenticated SECURITY DEFINER RPC warnings for `redeem_promo_code`, `score_my_placement_attempt`. They contain own-user checks but require adversarial tests and explicit privilege review before closing.
- Leaked password protection is disabled; Supabase documents this as a Pro-plan feature.
- `password-login` currently keys attempts on email and supplied forwarded IP: spoof-resistance, atomic counters, and direct Supabase Auth bypass require testing.
- Latest Flutter mobile code is partly stored in compressed source-handoff archives and has not been fully unpacked/built/tested in this pass.
- Staging/production parity for all latest functions, app configuration and legal/provider setup needs final deployment checks.
- Do not mark 100% production-ready without completing the above.

## Owner initialization
1. Set `OWNER_EMAIL` as a Supabase Edge Function secret in **both** projects. It must match a mailbox you control. Do not paste credentials into Git or conversation.
2. Sign up normally with that email and verify its email address. Use a strong unique password (10+ characters).
3. Complete the one-time `owner-bootstrap` authenticated flow in the Flutter client. Verify both `user_roles` and `admin_users` have the same one owner identity.
4. Enroll authenticator MFA and verify AAL2 before any admin action.
5. Verify a different user cannot become owner, change roles or access admin APIs. Confirm owner setup now returns 404.

## Critical negative tests
- Unauthenticated caller, verified normal user, MFA AAL1 admin, MFA AAL2 owner: test each sensitive API action.
- Simultaneous first-owner claim attempts from unrelated accounts; expect exactly one valid `OWNER_EMAIL` claim.
- Direct REST table read/write by arbitrary users against someone else's data.
- Bruteforce 6 concurrent wrong password attempts across spoofed headers; check lockout and audit logs.
- Session revocation, password reset, deletion, signup, notifications, premium purchase and restore on a physical phone.

**Status: Partial security closure, release NOT approved.**
