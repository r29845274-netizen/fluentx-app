from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
path = root / 'lib/features/learn/presentation/screens/learn_hub_screen.dart'
if not path.exists():
    raise SystemExit(f'Learn hub screen not found: {path}')

code = path.read_text()
old = "final position = (_currentWeek / 60).clamp(0.0, 1.0);"
new = "final position = (_currentWeek / 60).clamp(0.0, 1.0).toDouble();"
if old in code:
    code = code.replace(old, new, 1)

# Keep the roadmap compatible even if the Flutter SDK lacks SliverList.separated.
old_sliver = """sliver: SliverList.separated(\n              itemCount: _visibleWeeks.length,\n              separatorBuilder: (_, __) => const SizedBox(height: AppSpacing.sm),\n              itemBuilder: (context, index) {"""
new_sliver = """sliver: SliverList.builder(\n              itemCount: _visibleWeeks.length,\n              itemBuilder: (context, index) {"""
if old_sliver in code:
    code = code.replace(old_sliver, new_sliver, 1)
    old_return = """                return _WeekCard(\n                  weekNumber: weekNo,"""
    new_return = """                return Padding(\n                  padding: EdgeInsets.only(bottom: index == _visibleWeeks.length - 1 ? 0 : AppSpacing.sm),\n                  child: _WeekCard(\n                  weekNumber: weekNo,"""
    code = code.replace(old_return, new_return, 1)
    old_close = """                  onTap: () => _openWeek(week),\n                );\n              },"""
    new_close = """                  onTap: () => _openWeek(week),\n                  ),\n                );\n              },"""
    code = code.replace(old_close, new_close, 1)

path.write_text(code)
print('Personalized learning path compile compatibility fix applied.')
