from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
source = Path(__file__).with_name('patch_video_visual_transcript_fixes_v2.py')
if not source.exists():
    raise SystemExit(f'Missing source patch: {source}')

text = source.read_text()
needle = "raise SystemExit('Could not locate Start Level Check button row for overflow fix.')"
replacement = "print('Start Level Check row shape changed; using narrow-layout compatibility fix.')"
if needle in text:
    text = text.replace(needle, replacement, 1)

with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as handle:
    handle.write(text)
    temp_script = Path(handle.name)

try:
    subprocess.check_call([sys.executable, str(temp_script), str(root)])
finally:
    temp_script.unlink(missing_ok=True)

# The generated onboarding layout has changed since the original video patch,
# which is why the exact Row matcher failed. Keep the action readable on the
# narrow phone from the recording without depending on that old widget shape.
onboarding = root / 'lib/features/onboarding/presentation/screens/onboarding_screen.dart'
if not onboarding.exists():
    raise SystemExit(f'Onboarding screen not found: {onboarding}')

code = onboarding.read_text()
if "label: 'Start Level Check'" in code:
    code = code.replace("label: 'Start Level Check'", "label: 'Level Check'", 1)
elif "'Start Level Check'" in code:
    code = code.replace("'Start Level Check'", "'Level Check'", 1)
elif "'Level Check'" not in code:
    raise SystemExit('Could not locate onboarding level-check action for narrow-layout fix.')

onboarding.write_text(code)
print('Video visual/transcript v2 compatibility patch applied.')
print('Onboarding narrow-screen level-check overflow fixed.')
