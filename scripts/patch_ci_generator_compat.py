from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
pubspec = root / 'pubspec.yaml'
if not pubspec.exists():
    raise SystemExit(f'pubspec not found: {pubspec}')

text = pubspec.read_text(encoding='utf-8')
text, br = re.subn(r'(?m)^\s*build_runner:\s*[^\n]+$', '  build_runner: ^2.4.15', text, count=1)
text, fr = re.subn(r'(?m)^\s*freezed:\s*[^\n]+$', '  freezed: ^2.5.8', text, count=1)
if br != 1:
    raise SystemExit('build_runner dependency not found in pubspec')
if fr != 1:
    raise SystemExit('freezed dependency not found in pubspec')
pubspec.write_text(text, encoding='utf-8')

print('CI generator stack normalized: build_runner ^2.4.15, freezed ^2.5.8.')
