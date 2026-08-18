from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')

colors_path = root / 'lib/core/theme/app_colors.dart'
radius_path = root / 'lib/core/constants/app_radius.dart'
theme_path = root / 'lib/core/theme/app_theme.dart'

for p in (colors_path, radius_path, theme_path):
    if not p.exists():
        raise SystemExit(f'Required design file not found: {p}')

colors = colors_path.read_text()
replacements = {
    'Color(0xFF2563EB)': 'Color(0xFF6D5DFB)',
    'Color(0xFF1D4ED8)': 'Color(0xFF5848E8)',
    'Color(0xFFF8FAFC)': 'Color(0xFFF9F8FF)',
    'Color(0xFFF1F5F9)': 'Color(0xFFF2EFFF)',
    'Color(0xFFE2E8F0)': 'Color(0xFFE7E2FA)',
    'Color(0xFF0F172A)': 'Color(0xFF19152B)',
    'Color(0xFF64748B)': 'Color(0xFF716B88)',
    'Color(0xFFCBD5E1)': 'Color(0xFFC8C1DE)',
    'Color(0xFF16A34A)': 'Color(0xFF20A56B)',
    'Color(0xFFDC2626)': 'Color(0xFFE5484D)',
    'Color(0xFFD97706)': 'Color(0xFFF0A53A)',
    'Color(0xFF3B82F6)': 'Color(0xFF8A7CFF)',
    'Color(0xFF60A5FA)': 'Color(0xFFA79DFF)',
    'Color(0xFF0B0F19)': 'Color(0xFF11101A)',
    'Color(0xFF151B28)': 'Color(0xFF1B1828)',
    'Color(0xFF1B2333)': 'Color(0xFF242035)',
    'Color(0xFF1F2937)': 'Color(0xFF353047)',
    'Color(0xFFF1F5F9)': 'Color(0xFFF6F3FF)',
    'Color(0xFF94A3B8)': 'Color(0xFFAAA3BE)',
    'Color(0xFF475569)': 'Color(0xFF625B76)',
    'Color(0xFF22C55E)': 'Color(0xFF45C98A)',
    'Color(0xFFEF4444)': 'Color(0xFFFF6B72)',
    'Color(0xFFF59E0B)': 'Color(0xFFFFB74D)',
}
for old, new in replacements.items():
    colors = colors.replace(old, new)
colors_path.write_text(colors)

radius = radius_path.read_text()
radius = radius.replace('static const double md = 14;', 'static const double md = 16;')
radius = radius.replace('static const double lg = 20;', 'static const double lg = 22;')
radius = radius.replace('static const double xl = 28;', 'static const double xl = 30;')
radius_path.write_text(radius)

theme = theme_path.read_text()
theme = theme.replace('minimumSize: const Size.fromHeight(52),', 'minimumSize: const Size.fromHeight(54),')
theme = theme.replace('height: 64,', 'height: 70,')
theme = theme.replace('indicatorColor: colorScheme.primary.withValues(alpha: 0.12),', 'indicatorColor: colorScheme.primary.withValues(alpha: 0.14),')
theme = theme.replace('selectedColor: colorScheme.primary.withValues(alpha: 0.12),', 'selectedColor: colorScheme.primary.withValues(alpha: 0.14),')
theme = theme.replace('elevation: 0,\n        margin: EdgeInsets.zero,\n        shape: RoundedRectangleBorder(', 'elevation: 1,\n        shadowColor: colorScheme.primary.withValues(alpha: 0.08),\n        margin: EdgeInsets.zero,\n        shape: RoundedRectangleBorder(', 1)
theme = theme.replace('visualDensity: VisualDensity.standard,', 'visualDensity: VisualDensity.comfortable,')
theme_path.write_text(theme)

print('FluentX premium visual design system applied.')
