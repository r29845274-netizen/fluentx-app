from pathlib import Path
import re, sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('fluentx_admin_secure')

# Production version metadata.
pubspec = root / 'pubspec.yaml'
text = pubspec.read_text()
text = re.sub(r'^version:\s*.*$', 'version: 1.0.0+1', text, flags=re.M)
pubspec.write_text(text)

# Keep in-app version label aligned with release metadata.
settings = root / 'lib/features/settings/presentation/screens/settings_screen.dart'
if settings.exists():
    s = settings.read_text()
    s = re.sub(r"trailing:\s*Text\('[^']*'\)", "trailing: Text('1.0.0')", s)
    settings.write_text(s)

print('Production readiness patch applied')
