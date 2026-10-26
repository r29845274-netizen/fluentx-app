#!/usr/bin/env python3
"""Guarded FluentX auth UX fixes; never bypasses email verification or MFA."""
from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "fluentx_admin_secure")/"lib"
router=root/"routes/app_router.dart"
login=root/"features/authentication/presentation/screens/login_screen.dart"
signup=root/"features/authentication/presentation/screens/signup_screen.dart"
datasource=root/"features/authentication/data/datasources/auth_remote_datasource.dart"

def edit(path,old,new,desc):
    s=path.read_text()
    if new in s:return
    if s.count(old)!=1:raise SystemExit(desc+": expected unique source marker")
    path.write_text(s.replace(old,new,1))

# Owner exists: start at ordinary login, preserve server-side owner and MFA.
edit(router,"initialLocation: RoutePaths.ownerSetup,",
     "initialLocation: RoutePaths.login,","initial login route")

# Current SMTP/OTP config cannot deliver a usable code. Keep password login.
edit(login,"""                Center(
                  child: TextButton(
                    onPressed: null,
                    child: Text(_useOtp ? 'Use password instead' : 'Use email OTP instead'),
                  ),
                ),""","""                const Center(
                  child: Padding(
                    padding: EdgeInsets.symmetric(vertical: 8),
                    child: Text('Email code login is temporarily unavailable. Use your password.'),
                  ),
                ),""","OTP switch")

# Providers are disabled on Supabase; tell users rather than opening a 400 page.
for page in (login,signup):
    for provider in ("Google","Apple"):
        edit(page,
             "onPressed: () => ref.read(authControllerProvider.notifier).signInWith"+provider+"(),",
             "onPressed: () { ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('"+
             provider+" sign-in is not configured yet. Use email and password.'))); },",
             provider+" disabled provider UX")

# Successful signup uses a confirmation link, not a guessed six-digit code.
s=signup.read_text()
marker="    if (!mounted || !ok) return;"
start=s.find("    context.push(",s.find(marker))
if start<0:raise SystemExit("Signup OTP redirect marker missing")
end=s.find("\n  }",start)
if end<0:raise SystemExit("Signup method boundary not found")
s=s[:start]+"""    await showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Confirm your email'),
        content: const Text(
          'Open the verification link sent to your email. '
          'Then return to FluentX and sign in using your password.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Go to Login'),
          ),
        ],
      ),
    );
    if (mounted) context.go(RoutePaths.login);"""+s[end:]
signup.write_text(s)

# Surface server configuration problems rather than wrongly blaming user codes.
s=datasource.read_text()
marker="  if (lower.contains('otp') || lower.contains('token')) {"
if marker not in s:raise SystemExit("Auth message mapping changed")
s=s.replace(marker,"""  if (lower.contains('unauthorized ip') ||
      lower.contains('smtp') ||
      lower.contains('error sending confirmation') ||
      lower.contains('sending confirmation email') ||
      lower.contains('error sending magic link')) {
    return 'Email delivery is currently unavailable. Email provider settings must be fixed before sign-up works.';
  }
  if (lower.contains('otp_disabled') ||
      lower.contains('signups not allowed for otp')) {
    return 'Email OTP is disabled. Please sign in using email and password.';
  }
"""+marker,1)
datasource.write_text(s)
print("AUTH_PROVIDER_SIGNUP_PATCH_APPLIED")
