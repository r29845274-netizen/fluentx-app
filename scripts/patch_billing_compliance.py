from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
pubspec = root / 'pubspec.yaml'
premium = root / 'lib/features/premium/presentation/screens/premium_screen.dart'

# Keep compatibility with the project's Dart >=3.4 constraint.
pub_text = pubspec.read_text(encoding='utf-8')
if 'url_launcher:' not in pub_text:
    marker = '  timezone: ^0.9.4\n'
    if marker not in pub_text:
        raise SystemExit('Could not locate utilities dependency block in pubspec.yaml')
    pub_text = pub_text.replace(marker, marker + '  url_launcher: ^6.3.1\n', 1)
    pubspec.write_text(pub_text, encoding='utf-8')

text = premium.read_text(encoding='utf-8')

launcher_import = "import 'package:url_launcher/url_launcher.dart';"
if launcher_import not in text:
    marker = "import 'package:flutter_riverpod/flutter_riverpod.dart';"
    if marker not in text:
        raise SystemExit('Premium screen import marker not found')
    text = text.replace(marker, marker + '\n' + launcher_import, 1)

helper = r'''
Future<void> _openGooglePlaySubscriptionManagement(BuildContext context) async {
  final uri = Uri.parse(
    'https://play.google.com/store/account/subscriptions?sku=fluentx_premium&package=io.fluentx.app',
  );

  try {
    final opened = await launchUrl(uri, mode: LaunchMode.externalApplication);
    if (!opened && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not open Google Play subscriptions.')),
      );
    }
  } catch (_) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not open Google Play subscriptions.')),
      );
    }
  }
}
'''

if 'Future<void> _openGooglePlaySubscriptionManagement' not in text:
    class_marker = 'class PremiumScreen extends ConsumerStatefulWidget {'
    idx = text.find(class_marker)
    if idx == -1:
        raise SystemExit('PremiumScreen class marker not found')
    text = text[:idx] + helper + '\n' + text[idx:]

# Add management link beside Restore Purchases for users who are not currently
# recognized as premium (useful for canceled/restored/out-of-app purchases).
restore_block = r'''                Center(
                  child: TextButton(
                    onPressed: purchaseState.isLoading
                        ? null
                        : () => ref.read(purchaseControllerProvider.notifier).restore(),
                    child: const Text('Restore Purchases'),
                  ),
                ),
'''
manage_after_restore = restore_block + r'''                Center(
                  child: TextButton(
                    onPressed: () => _openGooglePlaySubscriptionManagement(context),
                    child: const Text('Manage Google Play subscription'),
                  ),
                ),
'''
if "child: const Text('Manage Google Play subscription')" not in text:
    if restore_block not in text:
        raise SystemExit('Restore Purchases block not found')
    text = text.replace(restore_block, manage_after_restore, 1)

# Active Premium users get a direct management action too.
active_marker = r'''            if (expiry != null) ...[
              const SizedBox(height: AppSpacing.sm),
              Text(
                subscription.willRenew
                    ? 'Renews on ${expiry.day}/${expiry.month}/${expiry.year}'
                    : 'Active until ${expiry.day}/${expiry.month}/${expiry.year}',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ],
'''
active_replacement = active_marker + r'''            const SizedBox(height: AppSpacing.lg),
            OutlinedButton.icon(
              onPressed: () => _openGooglePlaySubscriptionManagement(context),
              icon: const Icon(Icons.open_in_new, size: 18),
              label: const Text('Manage subscription'),
            ),
'''
if "label: const Text('Manage subscription')" not in text:
    if active_marker not in text:
        raise SystemExit('Active subscription details block not found')
    text = text.replace(active_marker, active_replacement, 1)

premium.write_text(text, encoding='utf-8')
print('Applied FluentX Google Play billing compliance patch')
