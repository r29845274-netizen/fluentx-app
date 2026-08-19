from pathlib import Path
import base64
import sys
import zlib

payload = Path(__file__).resolve().parent / 'payloads' / 'reference_uiux_patch.b64'
if not payload.exists():
    raise SystemExit(f'Reference UI/UX payload not found: {payload}')

source = zlib.decompress(base64.b64decode(payload.read_text().strip())).decode('utf-8')
exec(compile(source, str(payload), 'exec'), {'__name__': '__main__', '__file__': str(payload)})
