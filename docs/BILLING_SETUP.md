# FluentX Billing Setup

## Locked identifiers

Use these exact identifiers everywhere so Google Play, RevenueCat, and the Flutter app stay aligned.

- Android package: `io.fluentx.app`
- Google Play subscription product ID: `fluentx_premium`
- Monthly base plan ID: `monthly`
- Annual base plan ID: `annual`
- RevenueCat premium entitlement ID: `premium`
- RevenueCat offering ID: `default`
- RevenueCat monthly package: `$rc_monthly`
- RevenueCat annual package: `$rc_annual`
- Google Play one-time product ID: `fluentx_final_certificate_lifetime`
- RevenueCat lifetime certificate entitlement ID: `certificate_lifetime`
- Recommended India certificate price: `₹299` one-time

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

Create a separate one-time in-app product:

- Product ID: `fluentx_final_certificate_lifetime`
- Product type: non-consumable / one-time product
- India price: `₹299`
- Purpose: lets Free members permanently unlock the earned final Communication Mastery certificate PDF/download/share access.

Monthly and Annual subscribers must not be charged separately for the final certificate; active `premium` entitlement includes it.

Optional introductory trials/offers should be configured in Google Play. The app intentionally does not hardcode a free-trial duration; Google Play decides eligibility and shows the actual terms.

Before production billing tests, upload a signed AAB to at least an internal testing track and add licensed testers.

## RevenueCat

Create/add the Android app using package `io.fluentx.app`.

Import Google Play subscription `fluentx_premium` and its monthly/annual base plans.

Create entitlement:
- ID: `premium`

Attach both subscription options to entitlement `premium`.

Import the one-time Google Play product:
- `fluentx_final_certificate_lifetime`

Create entitlement:
- ID: `certificate_lifetime`

Attach the one-time certificate product to `certificate_lifetime`.

Create current offering:
- Offering ID: `default`

Attach packages:
- `$rc_monthly` -> `fluentx_premium:monthly`
- `$rc_annual` -> `fluentx_premium:annual`
- A lifetime/non-consumable package -> `fluentx_final_certificate_lifetime`

The Flutter app reads RevenueCat's current offering and maps annual packages to the Yearly UI and other recurring packages to Monthly. Certificate purchase lookup accepts a lifetime package or a package/product identifier containing both `certificate` and `lifetime`.

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
- Paywall and certificate prices come from Google Play through RevenueCat.
- Free users can earn the final certificate and unlock its PDF/download/share access for a one-time lifetime payment.
- Monthly and Annual subscribers receive final certificate access at no extra charge while the premium entitlement is active.
- A successful `certificate_lifetime` purchase remains available to that account even after premium subscription expiry.
- Trial wording is store-driven, not hardcoded.
- Restore Purchases is available.
- Google Play subscription management is available from the Premium screen.
- Premium access is granted only when RevenueCat entitlement `premium` is active.
