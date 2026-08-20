# FluentX — Google Play Data Safety Worksheet

Use this as the release-source-of-truth when completing Play Console. Re-check against the final production build and all enabled SDKs immediately before submission.

## App account and deletion
- Account creation: Yes (Supabase Auth / Google sign-in / email flows).
- In-app deletion path: Settings → Delete Account.
- In-app deletion implementation: authenticated `delete-account` Supabase Edge Function, followed by sign-out.
- External deletion web resource: REQUIRED before Play submission. It must work without reinstalling the app and must prominently identify FluentX/developer and provide a deletion request pathway.

## Data categories likely collected/processed
### Personal info
- Name / display name — profile and personalization.
- Email address — authentication/account management.
- User ID — Supabase account identifier; may also be used to associate RevenueCat subscription state.

### App activity / user content
- Learning progress, XP, streak/goals, achievements.
- Vocabulary/grammar/listening/writing activity and answers.
- Writing text submitted for AI scoring.
- AI practice chat content.
- Interview practice answer text/transcripts and scores.
- Placement test answers and speaking transcript/feedback where used.

### Audio / voice
- Microphone/speech input may be processed when the user explicitly uses speaking/interview features. Verify final Android permissions and speech-to-text provider behavior before declaring exact collection/sharing.

### App info and performance
- Firebase Analytics may collect app interaction/analytics data if enabled in the production build.
- Firebase Crashlytics may collect crash diagnostics, device/app metadata and stack information if enabled.

### Device or other identifiers
- Firebase installation/analytics/messaging identifiers may be processed by Firebase SDKs.
- FCM token is stored for push notifications.
- RevenueCat uses an app user/customer identifier and purchase/subscription information.

### Purchase information
- Subscription/purchase status is processed via Google Play Billing / RevenueCat. Do not claim FluentX stores raw payment-card details.

## Third-party processors / SDKs present in source
- Supabase: authentication, database, edge functions.
- Google Firebase: Core, Messaging, Analytics, Crashlytics.
- RevenueCat: subscriptions/purchase entitlements.
- Google Gemini: server-side AI feedback through Supabase Edge Functions.
- Device/platform speech services through `speech_to_text` where invoked.

## Security declarations to verify before Play submission
- Data in transit: HTTPS/TLS for Supabase, Firebase, RevenueCat and AI APIs.
- Account deletion: available in-app and external web path must be published.
- Data deletion: ensure `delete-account` removes user-linked application data and auth identity, except any explicitly documented legitimate retention.
- Optional vs required data: voice/AI practice is user-initiated; authentication information is required for account functionality.

## Do NOT submit this worksheet blindly
Before the final Data Safety form, inspect the release AAB/manifest and confirm:
1. Which Firebase services are actually initialized in production.
2. Whether Analytics collection defaults are enabled.
3. Whether Crashlytics collection defaults are enabled.
4. Exact microphone permission and speech-service behavior.
5. Final RevenueCat offering/products and App User ID behavior.
6. Any additional SDK introduced after this worksheet was created.

Google Play requires the Data Safety form to match the app, SDK behavior, and privacy policy across distributed versions.
