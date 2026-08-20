# FluentX Release Signing Setup

This setup keeps the Android upload key and passwords out of GitHub source code and out of chat.

## One-time setup on Windows

1. Install Java 17+ and make sure `keytool` works in PowerShell.
2. Install GitHub CLI and authenticate:
   ```powershell
   gh auth login
   ```
3. Clone/open this repository locally.
4. From the repository root run:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\tools\setup_release_secrets.ps1
   ```
5. The script will:
   - create `.local-secrets/fluentx-upload-keystore.jks` if one does not exist,
   - prompt locally for the keystore password,
   - prompt locally for the RevenueCat public Android SDK key,
   - set these GitHub Actions secrets:
     - `FLUENTX_UPLOAD_KEYSTORE_B64`
     - `FLUENTX_UPLOAD_STORE_PASSWORD`
     - `FLUENTX_UPLOAD_KEY_PASSWORD`
     - `FLUENTX_UPLOAD_KEY_ALIAS`
     - `REVENUECAT_ANDROID_API_KEY`

## Critical backup rule

Back up both of these somewhere secure and offline:
- `fluentx-upload-keystore.jks`
- its password

Do not commit them to GitHub. Losing the upload key can make future Play Store releases difficult or impossible depending on Play App Signing/key-reset eligibility.

## Build the production AAB

After the secrets are configured:

1. Open GitHub → Actions.
2. Choose **FluentX Production AAB**.
3. Click **Run workflow**.
4. Download the `FluentX-production-aab` artifact after the workflow succeeds.

The release workflow validates that all required secrets exist before building.
