param(
  [string]$Repo = 'r29845274-netizen/fluentx-app',
  [string]$Alias = 'fluentx-upload'
)

$ErrorActionPreference = 'Stop'

function Require-Command([string]$Name, [string]$Help) {
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "$Name is required. $Help"
  }
}

Require-Command 'keytool' 'Install a JDK (Java 17+) and make sure keytool is on PATH.'
Require-Command 'gh' 'Install GitHub CLI from https://cli.github.com/ and run: gh auth login'

$root = Split-Path -Parent $PSScriptRoot
$secretDir = Join-Path $root '.local-secrets'
New-Item -ItemType Directory -Force -Path $secretDir | Out-Null
$keystore = Join-Path $secretDir 'fluentx-upload-keystore.jks'

if (Test-Path $keystore) {
  $answer = Read-Host 'Upload keystore already exists. Reuse it? (Y/n)'
  if ($answer -match '^[Nn]') {
    throw 'Stopped to avoid replacing an existing signing key.'
  }
} else {
  Write-Host 'Create a strong keystore password. It will not be written to the repo.' -ForegroundColor Cyan
  $storeSecure = Read-Host 'Keystore password' -AsSecureString
  $storePtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($storeSecure)
  try { $storePassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($storePtr) }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($storePtr) }

  if ([string]::IsNullOrWhiteSpace($storePassword) -or $storePassword.Length -lt 8) {
    throw 'Use a keystore password of at least 8 characters.'
  }

  & keytool -genkeypair `
    -v `
    -keystore $keystore `
    -storetype JKS `
    -keyalg RSA `
    -keysize 2048 `
    -validity 10000 `
    -alias $Alias `
    -storepass $storePassword `
    -keypass $storePassword `
    -dname 'CN=FluentX Upload Key, OU=Mobile, O=FluentX, L=Agra, ST=Uttar Pradesh, C=IN'

  if ($LASTEXITCODE -ne 0) { throw 'keytool failed to create the upload keystore.' }
}

if (-not $storePassword) {
  $storeSecure = Read-Host 'Existing keystore password' -AsSecureString
  $storePtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($storeSecure)
  try { $storePassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($storePtr) }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($storePtr) }
}

Write-Host 'Enter your RevenueCat PUBLIC Android SDK key (starts with goog_). Do not use a secret/server key.' -ForegroundColor Cyan
$revenueCatKey = Read-Host 'RevenueCat Android SDK key'
if ([string]::IsNullOrWhiteSpace($revenueCatKey)) { throw 'RevenueCat Android SDK key is required.' }

$bytes = [System.IO.File]::ReadAllBytes($keystore)
$keystoreB64 = [Convert]::ToBase64String($bytes)

Write-Host "Setting repository Actions secrets for $Repo ..." -ForegroundColor Cyan
$keystoreB64 | gh secret set FLUENTX_UPLOAD_KEYSTORE_B64 --repo $Repo
$storePassword | gh secret set FLUENTX_UPLOAD_STORE_PASSWORD --repo $Repo
$storePassword | gh secret set FLUENTX_UPLOAD_KEY_PASSWORD --repo $Repo
$Alias | gh secret set FLUENTX_UPLOAD_KEY_ALIAS --repo $Repo
$revenueCatKey | gh secret set REVENUECAT_ANDROID_API_KEY --repo $Repo

Write-Host ''
Write-Host 'Release secrets configured successfully.' -ForegroundColor Green
Write-Host "Keystore backup location: $keystore" -ForegroundColor Yellow
Write-Host 'BACK UP THIS JKS FILE AND ITS PASSWORD OFFLINE. Losing it can block future Play Store updates.' -ForegroundColor Yellow
Write-Host 'The Production AAB workflow can now be run from GitHub Actions.' -ForegroundColor Green
