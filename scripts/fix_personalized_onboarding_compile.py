from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
path = root / 'lib/features/onboarding/presentation/screens/onboarding_screen.dart'
if not path.exists():
    raise SystemExit(f'Onboarding screen not found: {path}')

code = path.read_text()
marker = "import '../../../../core/constants/app_spacing.dart';\n"
needed = "import '../../../../core/router/onboarding_status_provider.dart';\n"
if needed not in code:
    if marker not in code:
        raise SystemExit('Could not locate onboarding import marker')
    code = code.replace(marker, marker + needed, 1)

path.write_text(code)
print('Personalized onboarding compile fix applied.')
