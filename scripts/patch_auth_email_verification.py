#!/usr/bin/env python3
"""Build-time patch for FluentX's email verification / localhost callback regression.

Applies to the extracted real Flutter source in the release workflows.
Fails closed if upstream changes, instead of silently shipping broken login.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "fluentx_admin_secure")
src = root / "lib/features/authentication/data/datasources/auth_remote_datasource.dart"
login = root / "lib/features/authentication/presentation/screens/login_screen.dart"
otp = root / "lib/features/authentication/presentation/screens/otp_verification_screen.dart"

for file in (src, login, otp):
    if not file.exists():
        raise SystemExit(f"Missing real auth source: {file}")

text = src.read_text()
if "static const _oauthRedirectUri = 'io.fluentx.app://login-callback';" not in text:
    raise SystemExit("Expected FluentX Android callback missing; review AndroidManifest and datasource")

# A default / localhost Site URL should not be used for Android confirmation links.
old_signup = """final response = await _client.auth.signUp(
        email: email,
        password: password,"""
new_signup = """final response = await _client.auth.signUp(
        email: email,
        password: password,
        emailRedirectTo: _oauthRedirectUri,"""
if old_signup in text:
    text = text.replace(old_signup, new_signup, 1)
elif new_signup not in text:
    raise SystemExit("Could not find signup call to add redirect")

old_login_otp = """await _client.auth.signInWithOtp(
        email: email,
        shouldCreateUser: false,"""
new_login_otp = """await _client.auth.signInWithOtp(
        email: email,
        shouldCreateUser: false,
        emailRedirectTo: _oauthRedirectUri,"""
count = text.count(old_login_otp)
if count:
    text = text.replace(old_login_otp, new_login_otp)
elif new_login_otp not in text:
    raise SystemExit("Could not find email OTP call to add redirect")

src.write_text(text)

# Password is the safe default until hosted Supabase templates send {{ .Token }}.
login_text = login.read_text()
if "bool _useOtp = true;" in login_text:
    login_text = login_text.replace("bool _useOtp = true;", "bool _useOtp = false;", 1)
elif "bool _useOtp = false;" not in login_text:
    raise SystemExit("Could not determine password-vs-OTP login default")
login.write_text(login_text)

# A user who verified using the old link can return to login instead of
# becoming stuck on a code screen. NEVER bypass Supabase identity verification.
screen = otp.read_text()
if "package:go_router/go_router.dart" not in screen:
    screen = screen.replace("import 'package:flutter/material.dart';",
                            "import 'package:flutter/material.dart';\nimport 'package:go_router/go_router.dart';", 1)
if "routes/route_paths.dart" not in screen:
    screen = screen.replace("import '../../../../core/error/failures.dart';",
                            "import '../../../../core/error/failures.dart';\nimport '../../../../routes/route_paths.dart';", 1)

old_help = "Check Inbox, Spam or Promotions. You can resend the email OTP when the timer ends."
new_help = "Check your Inbox or Spam. If you received a confirmation link instead of a 6-digit code, open it once, then return and sign in with your password."
if old_help in screen:
    screen = screen.replace(old_help, new_help, 1)
elif new_help not in screen:
    raise SystemExit("Unable to locate OTP help message")

if "Already confirmed? Sign in" not in screen:
    marker = """              const SizedBox(height: AppSpacing.sm),
              Center(
                child: Text(
                  '""" + new_help + """',"""
    if marker not in screen:
        raise SystemExit("OTP insertion point not found")
    snippet = """              if (widget.isSignup)
                Center(
                  child: TextButton(
                    onPressed: () => context.go(RoutePaths.login),
                    child: const Text('Already confirmed? Sign in'),
                  ),
                ),
"""
    screen = screen.replace(marker, snippet + marker, 1)
otp.write_text(screen)

assert "emailRedirectTo: _oauthRedirectUri" in src.read_text()
assert "bool _useOtp = false;" in login.read_text()
assert "Already confirmed? Sign in" in otp.read_text()
print("AUTH_EMAIL_PATCH_PASS: redirects, password default, signup fallback applied")
