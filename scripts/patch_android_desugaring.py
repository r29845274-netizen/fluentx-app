from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
gradle = root / 'android/app/build.gradle.kts'
if not gradle.exists():
    raise SystemExit(f'Android app Gradle file not found: {gradle}')

text = gradle.read_text()

if 'isCoreLibraryDesugaringEnabled = true' not in text:
    marker = '    compileOptions {\n'
    if marker not in text:
        raise SystemExit('compileOptions block not found in build.gradle.kts')
    text = text.replace(
        marker,
        marker + '        isCoreLibraryDesugaringEnabled = true\n',
        1,
    )

if 'coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:' not in text:
    text = text.rstrip() + '''\n\n// Required by flutter_local_notifications for Java 8+ APIs on older Android versions.\ndependencies {\n    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.0.3")\n}\n'''

gradle.write_text(text)

verified = gradle.read_text()
if 'isCoreLibraryDesugaringEnabled = true' not in verified:
    raise SystemExit('Failed to enable core library desugaring')
if 'coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.0.3")' not in verified:
    raise SystemExit('Failed to add desugar_jdk_libs dependency')

print('Android core-library desugaring enabled successfully.')
