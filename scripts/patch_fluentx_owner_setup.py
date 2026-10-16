#!/usr/bin/env python3
"""Apply a guarded, server-verified existing-owner login fix to extracted FluentX source."""
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else "fluentx_admin_secure")
owner = root / "lib/features/authentication/presentation/screens/owner_setup_screen.dart"
router = root / "lib/routes/app_router.dart"
fixed = Path(__file__).with_name("owner_setup_screen_fixed.dart")
for p in (owner, router, fixed):
    if not p.is_file():
        raise SystemExit(f"Missing required Flutter source: {p}")

old = owner.read_text(encoding="utf-8")
navigation = router.read_text(encoding="utf-8")
replacement = fixed.read_text(encoding="utf-8")
if ("owner-bootstrap-status" not in old
        or "class OwnerSetupScreen" not in old
        or "mode=owner" not in old):
    raise SystemExit("Owner source changed; aborting rather than corrupting app")
if ("functions.invoke('owner-bootstrap')" not in replacement
        or "functions.invoke('password-login'" not in replacement):
    raise SystemExit("Missing mandatory server-side identity/owner checks")
# Existing verified owners intentionally do not sign up again.
# Never require a new-account signup path in the one-time owner flow.
if "signUpWithEmail" in replacement:
    raise SystemExit("Unsafe owner flow: duplicate signup is forbidden")
needle = "      if (routerNotifier.isRecoveringPassword) {"
insertion = (
    "      // Keep owner setup on screen until its verified session and one-time\n"
    "      // server-side claim have completed; other routes retain MFA gates.\n"
    "      if (currentPath == RoutePaths.ownerSetup) return null;\n\n"
    + needle
)
if "Keep owner setup on screen" not in navigation:
    if needle not in navigation:
        raise SystemExit("Router no longer matches expected source")
    navigation = navigation.replace(needle, insertion, 1)
owner.write_text(replacement, encoding="utf-8")
router.write_text(navigation, encoding="utf-8")
print("OWNER_SETUP_EXISTING_ACCOUNT_FIX_APPLIED")
