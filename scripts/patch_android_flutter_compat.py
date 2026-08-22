from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
settings = root / 'android/settings.gradle.kts'
props = root / 'android/gradle.properties'

if not settings.exists():
    raise SystemExit(f'Android settings file not found: {settings}')

text = settings.read_text(encoding='utf-8')

# Keep Android toolchain on the versions used by the current Flutter template.
# AGP 9.1/Kotlin 2.4 can break Flutter plugins that still use the legacy KGP path.
text, agp_count = re.subn(
    r'id\("com\.android\.application"\) version "[^"]+" apply false',
    'id("com.android.application") version "9.0.1" apply false',
    text,
    count=1,
)
text, kotlin_count = re.subn(
    r'id\("org\.jetbrains\.kotlin\.android"\) version "[^"]+" apply false',
    'id("org.jetbrains.kotlin.android") version "2.3.20" apply false',
    text,
    count=1,
)
if agp_count != 1:
    raise SystemExit('Could not normalize Android Gradle Plugin version')
if kotlin_count != 1:
    raise SystemExit('Could not normalize Kotlin Gradle Plugin version')
settings.write_text(text, encoding='utf-8')

if props.exists():
    p = props.read_text(encoding='utf-8')
    def ensure(name: str, value: str) -> str:
        pattern = rf'(?m)^\s*{re.escape(name)}\s*=.*$'
        line = f'{name}={value}'
        if re.search(pattern, p):
            return re.sub(pattern, line, p)
        return p.rstrip() + '\n' + line + '\n'

    p = ensure('android.newDsl', 'false')
    # Flutter 3.44+ compatibility mode for plugins still applying legacy KGP.
    p = ensure('android.builtInKotlin', 'false')
    props.write_text(p, encoding='utf-8')

verified = settings.read_text(encoding='utf-8')
if 'com.android.application") version "9.0.1"' not in verified:
    raise SystemExit('AGP compatibility version was not applied')
if 'org.jetbrains.kotlin.android") version "2.3.20"' not in verified:
    raise SystemExit('Kotlin compatibility version was not applied')

print('Flutter Android toolchain normalized to AGP 9.0.1 / Kotlin 2.3.20 compatibility mode.')
