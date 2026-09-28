#!/usr/bin/env bash
set -euxo pipefail

rm -rf fluentx_admin_secure
rm -rf /tmp/fluentx_latest
rm -f /tmp/fluentx_latest.b64 /tmp/fluentx_recovered.tar /tmp/fluentx_overrides.tar.gz
mkdir -p /tmp/fluentx_latest

unzip -q fluentx_mobile_test_ready.zip

cat .source_handoff/2026-09-26-latest/part_*.b64 > /tmp/fluentx_latest.b64

python3 - <<'PY'
from pathlib import Path
import base64
import lzma

src = Path('/tmp/fluentx_latest.b64').read_text()
repair_index = 159817
if len(src) <= repair_index:
    raise SystemExit(f'latest source handoff too short: {len(src)}')

src = src[:repair_index] + src[repair_index + 1:]
raw = base64.b64decode(src, validate=True)

dec = lzma.LZMADecompressor()
chunks = []
try:
    for i in range(0, len(raw), 1024):
        chunks.append(dec.decompress(raw[i:i + 1024]))
except lzma.LZMAError:
    pass

out = b''.join(chunks)
if len(out) < 100000:
    raise SystemExit(f'recovered handoff unexpectedly small: {len(out)} bytes')

Path('/tmp/fluentx_recovered.tar').write_bytes(out)
print(f'recovered_tar_bytes={len(out)}')
PY

tar -xf /tmp/fluentx_recovered.tar -C /tmp/fluentx_latest || true

if [ ! -d /tmp/fluentx_latest/fluentx_admin_secure ]; then
  echo "Recovered handoff does not contain fluentx_admin_secure" >&2
  exit 31
fi

# This recovered file was truncated/corrupt in the staged handoff. Keep the
# corresponding file from the uploaded baseline ZIP instead.
rm -f /tmp/fluentx_latest/fluentx_admin_secure/lib/features/vocabulary/application/providers/vocabulary_providers.dart

rsync -a /tmp/fluentx_latest/fluentx_admin_secure/ fluentx_admin_secure/

base64 --decode   .source_handoff/2026-09-28-latest-overrides/override13.tar.gz.b64   > /tmp/fluentx_overrides.tar.gz

tar -xzf /tmp/fluentx_overrides.tar.gz -C .

test -f fluentx_admin_secure/pubspec.yaml
# Flutter stable currently resolves flutter_localizations to intl ^0.20.3.
# Align the uploaded source constraint so dependency solving can complete.
sed -i 's/intl: \^0\.19\.0/intl: ^0.20.3/' fluentx_admin_secure/pubspec.yaml

# Keep codegen on the last compatible Freezed 2.x release for the current Dart SDK.
sed -i 's/freezed: \\^2\\.5\\.5/freezed: ^2.5.2/' fluentx_admin_secure/pubspec.yaml

sed -i '/^[[:space:]]*freezed:/c\\  freezed: 2.5.2' fluentx_admin_secure/pubspec.yaml
echo "freezed_dependency=$(grep -E '^[[:space:]]*freezed:' fluentx_admin_secure/pubspec.yaml || true)"

# Apply latest compile compatibility fixes against current Flutter stable.
python3 - <<'PY'
from pathlib import Path

root = Path('fluentx_admin_secure')

# The legacy lucide_icons package subclasses IconData, which is final on current Flutter.
pub = root / 'pubspec.yaml'
text = pub.read_text()
text = text.replace('lucide_icons: ^0.257.0', 'lucide_icons_flutter: ^3.1.20')
pub.write_text(text)

for path in (root / 'lib').rglob('*.dart'):
    text = path.read_text()
    updated = text.replace(
        "package:lucide_icons/lucide_icons.dart",
        "package:lucide_icons_flutter/lucide_icons.dart",
    )
    if updated != text:
        path.write_text(updated)

# Supabase's current MFA API exposes totp as nullable.
admin = root / 'lib/features/admin/presentation/screens/admin_console_screen.dart'
if admin.exists():
    text = admin.read_text()
    text = text.replace(
        '_enrollmentQrCode = enrollment.totp.qrCode;\n'
        '        _enrollmentSecret = enrollment.totp.secret;',
        '_enrollmentQrCode = enrollment.totp?.qrCode;\n'
        '        _enrollmentSecret = enrollment.totp?.secret;\n'
        "        if (_enrollmentQrCode == null || _enrollmentSecret == null) {\n"
        "          throw StateError('TOTP enrollment details were not returned.');\n"
        '        }',
    )
    text = text.replace('Icons.visibility_lock', 'Icons.visibility_off_outlined')
    admin.write_text(text)

# Some reconstructed handoff files predate the uniform Failure message getter.
failures = root / 'lib/core/error/failures.dart'
if failures.exists():
    text = failures.read_text()
    if 'extension FailureUiMessage on Failure' not in text:
        text += """
\n/// Uniform access to the human-readable message across Failure variants.
extension FailureUiMessage on Failure {
  String get uiMessage => switch (this) {
        ServerFailure(:final message) => message,
        NetworkFailure(:final message) => message,
        AuthFailure(:final message) => message,
        CacheFailure(:final message) => message,
        UnexpectedFailure(:final message) => message,
      };
}
"""
        failures.write_text(text)

# flutter_local_notifications 17.x requires the iOS interpretation argument.
notifications = root / 'lib/core/services/notification_service.dart'
if notifications.exists():
    text = notifications.read_text()
    needle = '      androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,\n      matchDateTimeComponents: DateTimeComponents.time,'
    replacement = (
        '      androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,\n'
        '      uiLocalNotificationDateInterpretation: '
        'UILocalNotificationDateInterpretation.absoluteTime,\n'
        '      matchDateTimeComponents: DateTimeComponents.time,'
    )
    if needle in text and 'uiLocalNotificationDateInterpretation:' not in text:
        text = text.replace(needle, replacement)
        notifications.write_text(text)

print('latest compile compatibility fixes applied')
PY

echo "payments_dependency=$(grep -E '^[[:space:]]*purchases_flutter:' fluentx_admin_secure/pubspec.yaml || true)"
echo "intl_dependency=$(grep -E '^[[:space:]]*intl:' fluentx_admin_secure/pubspec.yaml || true)"

echo "latest_source_overlay=ok"
echo "dart_files=$(find fluentx_admin_secure/lib -type f -name '*.dart' | wc -l)"
echo "migrations=$(find fluentx_admin_secure/supabase/migrations -type f -name '*.sql' | wc -l)"
