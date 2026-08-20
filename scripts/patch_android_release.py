from pathlib import Path
import re, sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('fluentx_admin_secure')
android = root / 'android'
app = android / 'app'

# Force Play-ready API levels and configure release signing from key.properties.
kts = app / 'build.gradle.kts'
groovy = app / 'build.gradle'

if kts.exists():
    text = kts.read_text()
    if 'java.util.Properties' not in text:
        text = 'import java.util.Properties\nimport java.io.FileInputStream\n' + text
    if 'val keystoreProperties' not in text:
        marker = 'android {'
        signing = '''val keystoreProperties = Properties()\nval keystorePropertiesFile = rootProject.file("key.properties")\nif (keystorePropertiesFile.exists()) {\n    keystoreProperties.load(FileInputStream(keystorePropertiesFile))\n}\n\n'''
        text = text.replace(marker, signing + marker, 1)
    text = re.sub(r'compileSdk\s*=\s*flutter\.compileSdkVersion', 'compileSdk = 36', text)
    text = re.sub(r'targetSdk\s*=\s*flutter\.targetSdkVersion', 'targetSdk = 36', text)
    if 'signingConfigs {' not in text:
        anchor = '    defaultConfig {'
        block = '''    signingConfigs {\n        create("release") {\n            if (keystorePropertiesFile.exists()) {\n                keyAlias = keystoreProperties["keyAlias"] as String\n                keyPassword = keystoreProperties["keyPassword"] as String\n                storeFile = file(keystoreProperties["storeFile"] as String)\n                storePassword = keystoreProperties["storePassword"] as String\n            }\n        }\n    }\n\n'''
        text = text.replace(anchor, block + anchor, 1)
    # Replace default Flutter debug signing fallback only inside release block if present.
    text = text.replace('signingConfig = signingConfigs.getByName("debug")', 'signingConfig = signingConfigs.getByName("release")')
    kts.write_text(text)

elif groovy.exists():
    text = groovy.read_text()
    if 'def keystoreProperties' not in text:
        text = '''def keystoreProperties = new Properties()\ndef keystorePropertiesFile = rootProject.file('key.properties')\nif (keystorePropertiesFile.exists()) {\n    keystoreProperties.load(new FileInputStream(keystorePropertiesFile))\n}\n\n''' + text
    text = re.sub(r'compileSdkVersion\s+flutter\.compileSdkVersion', 'compileSdkVersion 36', text)
    text = re.sub(r'targetSdkVersion\s+flutter\.targetSdkVersion', 'targetSdkVersion 36', text)
    if 'signingConfigs {' not in text:
        anchor = '    defaultConfig {'
        block = '''    signingConfigs {\n        release {\n            keyAlias keystoreProperties['keyAlias']\n            keyPassword keystoreProperties['keyPassword']\n            storeFile keystoreProperties['storeFile'] ? file(keystoreProperties['storeFile']) : null\n            storePassword keystoreProperties['storePassword']\n        }\n    }\n\n'''
        text = text.replace(anchor, block + anchor, 1)
    text = text.replace('signingConfig signingConfigs.debug', 'signingConfig signingConfigs.release')
    groovy.write_text(text)
else:
    raise SystemExit('No Android app Gradle file found')

# Ensure secrets can never be committed accidentally.
gitignore = root / '.gitignore'
existing = gitignore.read_text() if gitignore.exists() else ''
for line in ['android/key.properties', 'android/app/upload-keystore.jks', '*.jks', '*.keystore']:
    if line not in existing:
        existing += ('\n' if existing and not existing.endswith('\n') else '') + line + '\n'
gitignore.write_text(existing)

print('Android release signing + API 36 patch applied')
