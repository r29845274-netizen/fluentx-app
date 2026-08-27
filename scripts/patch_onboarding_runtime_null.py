from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
path = root / 'lib/features/onboarding/presentation/screens/onboarding_screen.dart'
if not path.exists():
    raise SystemExit(f'Onboarding screen not found: {path}')

code = path.read_text()

# PageView builds its children eagerly. The placement page used forced null
# assertions for audience/goal even before the learner selected them, causing
# a startup red-screen for authenticated users whose onboarding is incomplete.
unsafe_page = '''                  _PlacementTestPage(
                    audienceKey: _selectedAudience!,
                    goalKey: _selectedGoal!,
                    onComplete: _finishOnboarding,
                  ),'''
safe_page = '''                  if (_selectedAudience != null && _selectedGoal != null)
                    _PlacementTestPage(
                      audienceKey: _selectedAudience!,
                      goalKey: _selectedGoal!,
                      onComplete: _finishOnboarding,
                    )
                  else
                    const SizedBox.shrink(),'''

if unsafe_page in code:
    code = code.replace(unsafe_page, safe_page, 1)
elif 'if (_selectedAudience != null && _selectedGoal != null)' not in code:
    raise SystemExit('Could not locate unsafe placement PageView child.')

# Also remove a second avoidable forced-null assertion if auth expires while
# a learner is taking the placement test.
unsafe_user = '''      final user = _client.auth.currentUser!;
      final q = _questions[_index];'''
safe_user = '''      final user = _client.auth.currentUser;
      if (user == null) {
        _showError('Your session expired. Please sign in again.');
        return;
      }
      final q = _questions[_index];'''
if unsafe_user in code:
    code = code.replace(unsafe_user, safe_user, 1)

required = [
    'if (_selectedAudience != null && _selectedGoal != null)',
    'else\n                    const SizedBox.shrink(),',
    "if (user == null) {\n        _showError('Your session expired. Please sign in again.');",
]
missing = [item for item in required if item not in code]
if missing:
    raise SystemExit('Runtime-null patch verification failed: ' + ', '.join(missing))

path.write_text(code)
print('Fixed onboarding eager PageView null crash and placement auth null assertion.')

# Apply the video-regression patch last so it sees the final generated auth,
# onboarding and theme files after the rest of the CI patch stack.
video_patch = Path(__file__).with_name('patch_video_regression_fixes.py')
if not video_patch.exists():
    raise SystemExit(f'Video regression patch not found: {video_patch}')
subprocess.check_call([sys.executable, str(video_patch), str(root)])

# The regression patch intentionally replaces large placement methods. Restore
# helper methods that the generated screen still references after that replace.
repair_patch = Path(__file__).with_name('repair_placement_helpers.py')
if not repair_patch.exists():
    raise SystemExit(f'Placement helper repair not found: {repair_patch}')
subprocess.check_call([sys.executable, str(repair_patch), str(root)])
