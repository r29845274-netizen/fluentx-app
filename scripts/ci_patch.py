from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
if not (root / 'pubspec.yaml').exists():
    raise SystemExit(f'Project root not found: {root}')


def replace(rel, old, new):
    path = root / rel
    if not path.exists():
        return
    text = path.read_text()
    if old in text:
        path.write_text(text.replace(old, new))


# Edit pubspec line-by-line so YAML indentation can never be consumed by regex.
pubspec = root / 'pubspec.yaml'
lines = pubspec.read_text().splitlines()
out = []
for line in lines:
    stripped = line.strip()
    if stripped.startswith('lucide_icons:') or stripped.startswith('flutter_lucide:'):
        continue
    if stripped.startswith('purchases_flutter:'):
        line = '  purchases_flutter: 10.5.0 # RevenueCat'
    elif stripped.startswith('intl:'):
        line = '  intl: ^0.20.3'
    elif stripped.startswith('build_runner:'):
        line = '  build_runner: 2.4.11'
    elif stripped.startswith('freezed:') and not stripped.startswith('freezed_annotation:'):
        line = '  freezed: 2.5.2'
    elif (
        stripped.startswith('riverpod_generator:')
        or stripped.startswith('json_serializable:')
        or stripped.startswith('hive_generator:')
    ):
        continue
    out.append(line)
pubspec.write_text('\n'.join(out) + '\n')

# RevenueCat 10.x API compatibility.
purchase = root / 'lib/features/premium/data/datasources/purchase_remote_datasource.dart'
if purchase.exists():
    code = purchase.read_text()
    code = code.replace(
        'final result = await Purchases.purchasePackage(package);',
        'final result = await Purchases.purchase(PurchaseParams.package(package));',
    )
    code = code.replace(
        "    } on PurchasesErrorCode catch (e) {\n      throw ServerException(e.toString());\n    } catch (e) {\n      throw ServerException(e.toString());\n    }",
        "    } catch (e) {\n      throw ServerException(e.toString());\n    }",
    )
    purchase.write_text(code)

# Remove old Lucide dependency usage and use stable Material icons.
icon_map = {
    'award': 'workspace_premium_outlined',
    'barChart2': 'bar_chart',
    'bell': 'notifications_none',
    'bookOpen': 'menu_book_outlined',
    'briefcase': 'work_outline',
    'building2': 'business_outlined',
    'check': 'check',
    'checkCircle2': 'check_circle_outline',
    'chevronRight': 'chevron_right',
    'clock': 'schedule',
    'construction': 'construction',
    'crown': 'workspace_premium_outlined',
    'eye': 'visibility_outlined',
    'eyeOff': 'visibility_off_outlined',
    'fileText': 'description_outlined',
    'flame': 'local_fire_department_outlined',
    'footprints': 'directions_walk',
    'graduationCap': 'school_outlined',
    'headphones': 'headphones_outlined',
    'helpCircle': 'help_outline',
    'home': 'home_outlined',
    'inbox': 'inbox_outlined',
    'info': 'info_outline',
    'languages': 'translate',
    'lifeBuoy': 'support_agent',
    'lightbulb': 'lightbulb_outline',
    'lock': 'lock_outline',
    'logOut': 'logout',
    'mailCheck': 'mark_email_read_outlined',
    'messageCircle': 'chat_bubble_outline',
    'messageSquare': 'chat_outlined',
    'mic': 'mic_none',
    'moon': 'dark_mode_outlined',
    'partyPopper': 'celebration_outlined',
    'pause': 'pause',
    'penLine': 'edit_outlined',
    'play': 'play_arrow',
    'playCircle': 'play_circle_outline',
    'refreshCw': 'refresh',
    'rotateCcw': 'replay',
    'search': 'search',
    'settings': 'settings_outlined',
    'shield': 'shield_outlined',
    'smartphone': 'smartphone',
    'sparkles': 'auto_awesome_outlined',
    'spellCheck': 'spellcheck',
    'square': 'crop_square',
    'star': 'star_border',
    'sun': 'light_mode_outlined',
    'target': 'gps_fixed',
    'trash2': 'delete_outline',
    'trophy': 'emoji_events_outlined',
    'user': 'person_outline',
    'userCog': 'manage_accounts_outlined',
    'users': 'group_outlined',
    'wifiOff': 'wifi_off',
    'x': 'close',
}

for path in (root / 'lib').rglob('*.dart'):
    code = path.read_text()
    if 'LucideIcons.' not in code and 'lucide_icons' not in code and 'flutter_lucide' not in code:
        continue
    code = code.replace("import 'package:lucide_icons/lucide_icons.dart';\n", '')
    code = code.replace("import 'package:flutter_lucide/flutter_lucide.dart';\n", '')
    if 'LucideIcons.' in code and "package:flutter/material.dart" not in code:
        if "import 'package:flutter/widgets.dart';" in code:
            code = code.replace(
                "import 'package:flutter/widgets.dart';",
                "import 'package:flutter/material.dart';",
            )
        else:
            code = "import 'package:flutter/material.dart';\n" + code
    for old, new in icon_map.items():
        code = code.replace(f'LucideIcons.{old}', f'Icons.{new}')
    code = re.sub(r'LucideIcons\.[A-Za-z0-9_]+', 'Icons.help_outline', code)
    path.write_text(code)

# Failure extension import.
ai_hub = root / 'lib/features/ai_practice/presentation/screens/ai_practice_hub_screen.dart'
if ai_hub.exists():
    code = ai_hub.read_text()
    marker = "import '../../../../core/constants/app_spacing.dart';\n"
    if 'core/error/failures.dart' not in code:
        code = code.replace(
            marker,
            marker + "import '../../../../core/error/failures.dart';\n",
        )
    ai_hub.write_text(code)

# Supabase MFA null-safety.
admin = root / 'lib/features/admin/presentation/screens/admin_console_screen.dart'
if admin.exists():
    code = admin.read_text()
    code = code.replace(
        "        _enrollmentFactorId = enrollment.id;\n        _enrollmentQrCode = enrollment.totp.qrCode;\n        _enrollmentSecret = enrollment.totp.secret;",
        "        final totp = enrollment.totp;\n        if (totp == null) {\n          throw const AuthException('Authenticator enrollment did not return TOTP details.');\n        }\n        _enrollmentFactorId = enrollment.id;\n        _enrollmentQrCode = totp.qrCode;\n        _enrollmentSecret = totp.secret;",
    )
    code = code.replace(
        "throw AuthException('No authenticator factor found.');",
        "throw const AuthException('No authenticator factor found.');",
    )
    code = code.replace(
        'const Icon(Icons.visibility_lock)',
        'const Icon(Icons.visibility)',
    )
    admin.write_text(code)

# flutter_local_notifications 17.x required parameter.
notifications = root / 'lib/core/services/notification_service.dart'
if notifications.exists():
    code = notifications.read_text()
    marker = '      androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,\n'
    if 'uiLocalNotificationDateInterpretation:' not in code:
        code = code.replace(
            marker,
            marker
            + '      uiLocalNotificationDateInterpretation:\n'
            + '          UILocalNotificationDateInterpretation.absoluteTime,\n',
        )
    notifications.write_text(code)

replace(
    'lib/app/app.dart',
    'Purchases.logIn(user.id).catchError((_) {});',
    'Purchases.logIn(user.id).then<void>((_) {}, onError: (_, __) {});',
)
replace(
    'lib/app/app.dart',
    'Purchases.logOut().catchError((_) {});',
    'Purchases.logOut().then<void>((_) {}, onError: (_, __) {});',
)

# Supabase current API.
main = root / 'lib/main.dart'
if main.exists():
    code = main.read_text().replace("import 'dart:ui';\n\n", '')
    code = code.replace(
        '    anonKey: EnvConfig.supabaseAnonKey,',
        '    publishableKey: EnvConfig.supabaseAnonKey,',
    )
    main.write_text(code)

# Safe cleanup already identified by CI.
replace(
    'lib/features/listening/application/providers/listening_providers.dart',
    "import '../../../authentication/application/providers/auth_providers.dart';\n",
    '',
)
replace(
    'lib/features/onboarding/application/providers/onboarding_providers.dart',
    "import '../../../../core/error/failures.dart';\n",
    '',
)
replace(
    'lib/features/authentication/presentation/screens/login_screen.dart',
    '      context.push(\n',
    '      await context.push(\n',
)
replace(
    'lib/features/authentication/presentation/screens/signup_screen.dart',
    '    context.push(\n',
    '    await context.push(\n',
)

# Hard sanity checks.
text = pubspec.read_text()
if re.search(r'(?m)^\S.*flutter_svg:', text):
    raise SystemExit('pubspec indentation damaged near flutter_svg')
leftovers = []
for path in (root / 'lib').rglob('*.dart'):
    code = path.read_text()
    if (
        'LucideIcons.' in code
        or 'package:lucide_icons/' in code
        or 'package:flutter_lucide/' in code
    ):
        leftovers.append(str(path))
if leftovers:
    raise SystemExit('Lucide leftovers: ' + ', '.join(leftovers))

print('CI compatibility patch applied successfully.')
