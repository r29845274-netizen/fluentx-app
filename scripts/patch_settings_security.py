from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
path = root / 'lib/features/settings/presentation/screens/settings_screen.dart'
text = path.read_text(encoding='utf-8')
block = """                  ProfileMenuTile(\n                    icon: Icons.shield_outlined,\n                    label: 'Admin Console',\n                    onTap: () => context.push(RoutePaths.adminConsole),\n                  ),\n                  const Divider(height: 1),\n"""
if block in text:
    text = text.replace(block, '')
path.write_text(text, encoding='utf-8')
print(f'Updated {path}')
