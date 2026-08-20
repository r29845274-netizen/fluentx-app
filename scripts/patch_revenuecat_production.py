#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
main = root / 'lib/main.dart'
env = root / 'lib/core/config/env_config.dart'

if not main.exists():
    raise SystemExit('main.dart not found')

main_text = main.read_text()

# Ensure RevenueCat import exists.
if "package:purchases_flutter/purchases_flutter.dart" not in main_text:
    marker = "import 'package:flutter/material.dart';"
    if marker in main_text:
        main_text = main_text.replace(marker, marker + "\nimport 'package:purchases_flutter/purchases_flutter.dart';")
    else:
        main_text = "import 'package:purchases_flutter/purchases_flutter.dart';\n" + main_text

# Ensure Environment import exists.
env_import = "import 'core/config/env_config.dart';"
if env_import not in main_text:
    imports = main_text.splitlines()
    insert_at = 0
    for i, line in enumerate(imports):
        if line.startswith('import '):
            insert_at = i + 1
    imports.insert(insert_at, env_import)
    main_text = '\n'.join(imports) + ('\n' if not main_text.endswith('\n') else '')

helper = r'''
Future<void> _configureRevenueCat() async {
  final apiKey = EnvConfig.revenueCatAndroidApiKey;
  if (apiKey.isEmpty) {
    // Billing stays disabled until a public RevenueCat Android SDK key is
    // supplied via --dart-define. Never hardcode private/server keys here.
    return;
  }

  const flavor = String.fromEnvironment('FLAVOR', defaultValue: 'dev');
  await Purchases.setLogLevel(
    flavor == 'prod' ? LogLevel.info : LogLevel.debug,
  );
  await Purchases.configure(PurchasesConfiguration(apiKey));
}
'''

if 'Future<void> _configureRevenueCat()' not in main_text:
    idx = main_text.find('Future<void> main(')
    if idx == -1:
        idx = main_text.find('void main(')
    if idx == -1:
        raise SystemExit('main() not found')
    main_text = main_text[:idx] + helper + '\n' + main_text[idx:]

# Inject configure call after WidgetsFlutterBinding.ensureInitialized if possible,
# otherwise as the first await-safe statement inside an async main.
if 'await _configureRevenueCat();' not in main_text:
    binding = 'WidgetsFlutterBinding.ensureInitialized();'
    if binding in main_text:
        main_text = main_text.replace(binding, binding + '\n  await _configureRevenueCat();', 1)
    else:
        main_text = main_text.replace('Future<void> main() async {', 'Future<void> main() async {\n  WidgetsFlutterBinding.ensureInitialized();\n  await _configureRevenueCat();', 1)

main.write_text(main_text)

# Add a single source of truth for public build-time RevenueCat key.
if env.exists():
    env_text = env.read_text()
    if 'revenueCatAndroidApiKey' not in env_text:
        class_pos = env_text.find('class EnvConfig')
        brace = env_text.find('{', class_pos)
        if brace != -1:
            env_text = env_text[:brace+1] + r'''
  /// Public RevenueCat Android SDK key. Supply at build time:
  /// --dart-define=REVENUECAT_ANDROID_API_KEY=goog_...
  static const revenueCatAndroidApiKey = String.fromEnvironment(
    'REVENUECAT_ANDROID_API_KEY',
    defaultValue: '',
  );
''' + env_text[brace+1:]
        env.write_text(env_text)
else:
    env.parent.mkdir(parents=True, exist_ok=True)
    env.write_text(r'''class EnvConfig {
  static const revenueCatAndroidApiKey = String.fromEnvironment(
    'REVENUECAT_ANDROID_API_KEY',
    defaultValue: '',
  );
}
''')

print('RevenueCat production bootstrap patched')
