# FluentX — Final Launch Checklist

This file separates work that is already prepared in the repository from steps that require external production accounts or final device testing.

## Repository / code preparation
- [x] Production AAB workflow exists.
- [x] Release signing setup script exists.
- [x] RevenueCat production bootstrap exists.
- [x] Google Play billing compliance patch exists.
- [x] Final UI cleanup and visual consistency patches exist.
- [x] Release legal/privacy copy is patched into the app.
- [x] Android package is locked to `io.fluentx.app`.
- [x] Billing identifiers are locked in `docs/BILLING_SETUP.md`.
- [x] Production workflow runs source preflight, code generation, analysis, tests and AAB build.
- [x] Production Android audit applies the actual release patch stack.
- [x] Play Data Safety worksheet exists.
- [x] External account deletion page template exists.
- [x] Play Store listing copy draft exists.

## External setup — intentionally deferred until Play Console / launch phase
- [ ] Complete Google Play Console developer registration.
- [ ] Create FluentX application in Play Console using package `io.fluentx.app`.
- [ ] Add RevenueCat service account to Play Console with required app/billing permissions.
- [ ] Upload the Google service-account JSON directly to RevenueCat. Never commit it to GitHub.
- [ ] Create Google Play subscription product `fluentx_premium`.
- [ ] Create base plans `monthly` and `annual`.
- [ ] Import both subscription options into RevenueCat.
- [ ] Confirm entitlement `premium` and offering `default`.
- [ ] Obtain the RevenueCat public Android SDK key beginning with `goog_`.
- [ ] Run `tools/setup_release_secrets.ps1` locally and set the five GitHub Actions secrets.
- [ ] Back up the upload JKS and password offline.
- [ ] Publish Privacy Policy and Account Deletion URLs on a public web page before Play submission.
- [ ] Complete Play Console Data Safety, content rating and app-access declarations from the final build.
- [ ] Upload a signed AAB to an allowed testing track.
- [ ] Add licensed billing testers.
- [ ] Complete any Google-required testing period/account verification for the developer account type in effect at launch time.

## Final runtime / device testing — do after external production configuration
- [ ] Fresh install and first launch.
- [ ] Sign-up, sign-in and sign-out.
- [ ] Google/email authentication callback.
- [ ] Placement test end-to-end.
- [ ] Personalized learning path.
- [ ] Vocabulary, grammar, listening and writing flows.
- [ ] Microphone permission and speaking flow on a physical Android device.
- [ ] Interview AI Coach end-to-end.
- [ ] Notifications permission and delivery behavior.
- [ ] Premium paywall displays live Google Play prices.
- [ ] Monthly purchase.
- [ ] Annual purchase.
- [ ] Restore purchases.
- [ ] Subscription management link.
- [ ] Expired/cancelled entitlement handling.
- [ ] Account deletion in-app.
- [ ] External account-deletion route.
- [ ] Offline / weak-network error handling.
- [ ] Crash-free smoke test on at least one lower-end and one current Android device.

## Release rule
Do not run the production AAB workflow until all required GitHub release secrets exist. Do not submit Data Safety declarations from assumptions; verify the final production AAB and enabled SDK behavior first.
