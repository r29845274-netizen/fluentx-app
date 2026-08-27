from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
path = root / 'lib/features/onboarding/presentation/screens/onboarding_screen.dart'
if not path.exists():
    raise SystemExit(f'Onboarding screen not found: {path}')

code = path.read_text()

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

video_patch = Path(__file__).with_name('patch_video_regression_fixes.py')
if not video_patch.exists():
    raise SystemExit(f'Video regression patch not found: {video_patch}')
subprocess.check_call([sys.executable, str(video_patch), str(root)])

repair_patch = Path(__file__).with_name('repair_placement_helpers.py')
if not repair_patch.exists():
    raise SystemExit(f'Placement helper repair not found: {repair_patch}')
subprocess.check_call([sys.executable, str(repair_patch), str(root)])

runtime_patch = Path(__file__).with_name('patch_runtime_screenshot_regressions.py')
if not runtime_patch.exists():
    raise SystemExit(f'Runtime screenshot patch not found: {runtime_patch}')
subprocess.check_call([sys.executable, str(runtime_patch), str(root)])

theme_patch = Path(__file__).with_name('patch_theme_preferences.py')
if not theme_patch.exists():
    raise SystemExit(f'Theme preference patch not found: {theme_patch}')
subprocess.check_call([sys.executable, str(theme_patch), str(root)])
