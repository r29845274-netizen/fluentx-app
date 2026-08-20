# FluentX Billing Setup

## Locked identifiers

Use these exact identifiers everywhere so Google Play, RevenueCat, and the Flutter app stay aligned.

- Android package: `io.fluentx.app`
- Google Play subscription product ID: `fluentx_premium`
- Monthly base plan ID: `monthly`
- Annual base plan ID: `annual`
- RevenueCat entitlement ID: `premium`
- RevenueCat offering ID: `default`
- RevenueCat monthly package: `$rc_monthly`
- RevenueCat annual package: `$rc_annual`

## Google Play Console

Create one auto-renewing subscription named FluentX Premium with product ID `fluentx_premium`.

Add two base plans:

1. `monthly`
   - Billing period: 1 month
   - Auto-renewing: enabled
   - Set market pricing in Play Console

2. `annual`
   - Billing period: 1 year
   - Auto-renewing: enabled
   - Set market pricing in Play Console

Optional introductory trials/offers should be configured in Google Play. The app intentionally does not hardcode a free-trial duration; Google Play decides eligibility and shows the actual terms.

Before production billing tests, upload a signed AAB to at least an internal testing track and add licensed testers.

## RevenueCat

Create/add the Android app using package `io.fluentx.app`.

Import Google Play product `fluentx_premium` and its monthly/annual base plans.

Create entitlement:
- ID: `premium`

Attach both subscription options to entitlement `premium`.

Create current offering:
- Offering ID: `default`

Attach packages:
- `$rc_monthly` -> `fluentx_premium:monthly`
- `$rc_annual` -> `fluentx_premium:annual`

The Flutter app reads RevenueCat's current offering and maps annual packages to the Yearly UI and all other recurring packages to Monthly.

## GitHub repository secrets

Set these repository Actions secrets before a production AAB build:

- `REVENUECAT_ANDROID_API_KEY` — RevenueCat public Android SDK key (`goog_...`)
- `FLUENTX_UPLOAD_KEYSTORE_B64` — base64-encoded upload keystore
- `FLUENTX_UPLOAD_STORE_PASSWORD`
- `FLUENTX_UPLOAD_KEY_PASSWORD`
- `FLUENTX_UPLOAD_KEY_ALIAS`

Never commit the keystore or passwords to Git.

## In-app purchase behavior

- RevenueCat initializes once at app startup when the public Android SDK key is provided.
- Paywall prices come from Google Play through RevenueCat.
- Trial wording is store-driven, not hardcoded.
- Restore Purchases is available.
- Google Play subscription management is available from the Premium screen.
- Premium access is granted only when RevenueCat entitlement `premium` is active.
