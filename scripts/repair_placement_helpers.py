from pathlib import Path
import sys

# Final compile guard for video-regression placement changes.
root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
path = root / 'lib/features/onboarding/presentation/screens/onboarding_screen.dart'
if not path.exists():
    raise SystemExit(f'Onboarding screen not found: {path}')

code = path.read_text()
class_marker = 'class _PlacementTestPageState extends State<_PlacementTestPage> {\n'
if class_marker not in code:
    raise SystemExit('Placement test state class not found.')

helpers = r'''
  void _showError(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  String _audienceLabel() {
    for (final audience in _audiences) {
      if (audience.key == widget.audienceKey) return audience.label;
    }
    return widget.audienceKey.replaceAll('_', ' ');
  }

  String _goalLabel() {
    final goals = _goalsByAudience[widget.audienceKey] ?? const <_GoalOption>[];
    for (final goal in goals) {
      if (goal.key == widget.goalKey) return goal.label;
    }
    return widget.goalKey.replaceAll('_', ' ');
  }
'''

# The video-regression patch replaces a large section of the placement class.
# Restore these helper methods afterward if that replacement removed them.
missing = []
if 'void _showError(String message)' not in code:
    missing.append('showError')
if 'String _audienceLabel()' not in code:
    missing.append('audienceLabel')
if 'String _goalLabel()' not in code:
    missing.append('goalLabel')

if missing:
    code = code.replace(class_marker, class_marker + helpers, 1)

required = [
    'void _showError(String message)',
    'String _audienceLabel()',
    'String _goalLabel()',
]
left = [item for item in required if item not in code]
if left:
    raise SystemExit('Placement helper restoration failed: ' + ', '.join(left))

path.write_text(code)
print('Placement helper methods restored:', ', '.join(missing) if missing else 'already present')
