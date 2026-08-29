from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
home = root / 'lib/features/home/presentation/screens/home_screen.dart'
if not home.exists():
    raise SystemExit(f'Home screen not found: {home}')

text = home.read_text(encoding='utf-8')

old = """      child: ListView(\n        padding: const EdgeInsets.fromLTRB(16, 12, 16, 28),\n        children: [\n"""
new = """      child: ListView(\n        physics: const AlwaysScrollableScrollPhysics(),\n        keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,\n        padding: const EdgeInsets.fromLTRB(16, 12, 16, 120),\n        children: [\n"""

if old in text:
    text = text.replace(old, new, 1)
elif 'physics: const AlwaysScrollableScrollPhysics()' not in text:
    raise SystemExit('Home ListView marker not found')

home.write_text(text, encoding='utf-8')
print('Home scroll fix applied: always-scrollable with safe bottom navigation clearance.')
