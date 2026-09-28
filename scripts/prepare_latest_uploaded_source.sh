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

echo "payments_dependency=$(grep -E '^[[:space:]]*purchases_flutter:' fluentx_admin_secure/pubspec.yaml || true)"
echo "intl_dependency=$(grep -E '^[[:space:]]*intl:' fluentx_admin_secure/pubspec.yaml || true)"

echo "latest_source_overlay=ok"
echo "dart_files=$(find fluentx_admin_secure/lib -type f -name '*.dart' | wc -l)"
echo "migrations=$(find fluentx_admin_secure/supabase/migrations -type f -name '*.sql' | wc -l)"
