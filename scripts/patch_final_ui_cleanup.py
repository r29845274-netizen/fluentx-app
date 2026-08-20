from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')

# Remove the unused placeholder scaffold file so release source has no dead
# "feature not built" artifact.
bootstrap = root / 'lib/core/router/bootstrap_screen.dart'
if bootstrap.exists():
    bootstrap.unlink()

premium = root / 'lib/features/premium/presentation/screens/premium_screen.dart'
text = premium.read_text(encoding='utf-8')
text = text.replace("'7-day free trial, cancel anytime.'", "'Choose a plan below. Billing, trial eligibility and renewal details are confirmed by Google Play.'")
text = text.replace("label: 'Start Free Trial'", "label: 'Continue'")
premium.write_text(text, encoding='utf-8')

print('Applied FluentX final UI cleanup')
