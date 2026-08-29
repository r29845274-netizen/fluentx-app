from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
cert = root / 'lib/features/certificates/presentation/screens/certificates_screen.dart'
if not cert.exists():
    raise SystemExit('Certificates screen not found')

text = cert.read_text(encoding='utf-8')
text = text.replace("var certificatePrice = '₹499';", "var certificatePrice = '₹299';")
text = text.replace("row['certificate_price'] ?? '₹499'", "row['certificate_price'] ?? '₹299'")
cert.write_text(text, encoding='utf-8')
print('Final certificate fallback price set to ₹299 one-time.')
