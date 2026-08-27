import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../../core/constants/app_radius.dart';
import '../../../../core/constants/app_spacing.dart';
import '../../../../core/error/failures.dart';
import '../../../../shared/widgets/widgets.dart';
import '../../application/providers/purchase_providers.dart';
import '../../domain/entities/subscription_status.dart';


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

class PremiumScreen extends ConsumerStatefulWidget {
  const PremiumScreen({super.key});

  @override
  ConsumerState<PremiumScreen> createState() => _PremiumScreenState();
}

class _PremiumScreenState extends ConsumerState<PremiumScreen> {
  String? _selectedPackageId;

  static const _features = [
    'Unlimited AI Practice sessions',
    'Full Interview Skills module',
    'Full Listening library',
    'Writing module with AI rubric scoring',
    'Full Communication DNA + history',
    'Priority AI response speed',
  ];

  @override
  Widget build(BuildContext context) {
    final subscriptionAsync = ref.watch(subscriptionStatusProvider);
    final packagesAsync = ref.watch(premiumPackagesProvider);
    final purchaseState = ref.watch(purchaseControllerProvider);
    final colorScheme = Theme.of(context).colorScheme;

    ref.listen(purchaseControllerProvider, (previous, next) {
      final error = next.error;
      if (error is Failure) {
        ScaffoldMessenger.of(context)
          ..hideCurrentSnackBar()
          ..showSnackBar(SnackBar(content: Text(error.uiMessage)));
      }
    });

    return Scaffold(
      appBar: AppBar(title: const Text('Fluent X Premium')),
      body: SafeArea(
        top: false,
        child: subscriptionAsync.when(
          data: (subscription) {
            if (subscription.isPremium) return _AlreadyPremium(subscription: subscription);

            return ListView(
              padding: const EdgeInsets.all(AppSpacing.base),
              children: [
                Icon(Icons.workspace_premium_outlined, size: 48, color: const Color(0xFFD97706)),
                const SizedBox(height: AppSpacing.base),
                Text('Unlock your full potential', style: Theme.of(context).textTheme.displayLarge),
                const SizedBox(height: AppSpacing.sm),
                Text(
                  'Choose a plan below. Billing, trial eligibility and renewal details are confirmed by Google Play.',
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        color: colorScheme.onSurfaceVariant,
                      ),
                ),
                const SizedBox(height: AppSpacing.lg),
                for (final feature in _features)
                  Padding(
                    padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                    child: Row(
                      children: [
                        Icon(Icons.check_circle_outline, size: 18, color: colorScheme.primary),
                        const SizedBox(width: AppSpacing.sm),
                        Expanded(child: Text(feature)),
                      ],
                    ),
                  ),
                const SizedBox(height: AppSpacing.lg),
                packagesAsync.when(
                  data: (packages) {
                    if (packages.isEmpty) {
                      return const EmptyStateWidget(
                        title: 'Plans unavailable right now',
                        message: 'Please check back shortly.',
                      );
                    }
                    _selectedPackageId ??= packages.first.identifier;
                    return Column(
                      children: [
                        for (final pkg in packages)
                          Padding(
                            padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                            child: _PlanTile(
                              package: pkg,
                              isSelected: _selectedPackageId == pkg.identifier,
                              onTap: () => setState(() => _selectedPackageId = pkg.identifier),
                            ),
                          ),
                      ],
                    );
                  },
                  loading: () => const LoadingCardSkeleton(),
                  error: (_, __) => ErrorStateWidget(
                    onRetry: () => ref.invalidate(premiumPackagesProvider),
                  ),
                ),
                const SizedBox(height: AppSpacing.base),
                PrimaryButton(
                  label: 'Continue',
                  isLoading: purchaseState.isLoading,
                  onPressed: _selectedPackageId == null
                      ? null
                      : () => ref
                          .read(purchaseControllerProvider.notifier)
                          .buy(_selectedPackageId!),
                ),
                const SizedBox(height: AppSpacing.sm),
                Center(
                  child: TextButton(
                    onPressed: purchaseState.isLoading
                        ? null
                        : () => ref.read(purchaseControllerProvider.notifier).restore(),
                    child: const Text('Restore Purchases'),
                  ),
                ),
                Center(
                  child: TextButton(
                    onPressed: () => _openGooglePlaySubscriptionManagement(context),
                    child: const Text('Manage Google Play subscription'),
                  ),
                ),
              ],
            );
          },
          loading: () => const LoadingWidget(),
          error: (_, __) => ErrorStateWidget(
            onRetry: () => ref.invalidate(subscriptionStatusProvider),
          ),
        ),
      ),
    );
  }
}

class _PlanTile extends StatelessWidget {
  const _PlanTile({required this.package, required this.isSelected, required this.onTap});

  final PremiumPackage package;
  final bool isSelected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return InkWell(
      onTap: onTap,
      borderRadius: AppRadius.lgAll,
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.base),
        decoration: BoxDecoration(
          borderRadius: AppRadius.lgAll,
          border: Border.all(
            color: isSelected ? colorScheme.primary : colorScheme.outline,
            width: isSelected ? 2 : 1,
          ),
          color: isSelected ? colorScheme.primary.withValues(alpha: 0.05) : null,
        ),
        child: Row(
          children: [
            Radio<String>(
              value: package.identifier,
              groupValue: isSelected ? package.identifier : null,
              onChanged: (_) => onTap(),
            ),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    package.period == 'yearly' ? 'Yearly' : 'Monthly',
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                  ),
                  Text(package.priceString, style: Theme.of(context).textTheme.bodySmall),
                  const SizedBox(height: 3),
                  Text(
                    package.period == 'yearly'
                        ? 'ELITE ID • Mastery Certificate • Gold profile identity'
                        : 'PRO ID • Level certificates • Premium profile identity',
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                          fontWeight: FontWeight.w600,
                        ),
                  ),
                ],
              ),
            ),
            if (package.period == 'yearly')
              Container(
                padding: const EdgeInsets.symmetric(horizontal: AppSpacing.sm, vertical: 2),
                decoration: BoxDecoration(
                  color: const Color(0xFF16A34A).withValues(alpha: 0.12),
                  borderRadius: AppRadius.fullAll,
                ),
                child: const Text(
                  'Best Value',
                  style: TextStyle(color: Color(0xFF16A34A), fontSize: 11, fontWeight: FontWeight.w600),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _AlreadyPremium extends StatelessWidget {
  const _AlreadyPremium({required this.subscription});

  final SubscriptionStatus subscription;

  @override
  Widget build(BuildContext context) {
    final expiry = subscription.expirationDate;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.workspace_premium_outlined, size: 56, color: const Color(0xFFD97706)),
            const SizedBox(height: AppSpacing.base),
            Text("You're on Premium 🎉", style: Theme.of(context).textTheme.headlineLarge),
            if (expiry != null) ...[
              const SizedBox(height: AppSpacing.sm),
              Text(
                subscription.willRenew
                    ? 'Renews on ${expiry.day}/${expiry.month}/${expiry.year}'
                    : 'Active until ${expiry.day}/${expiry.month}/${expiry.year}',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ],
            const SizedBox(height: AppSpacing.lg),
            OutlinedButton.icon(
              onPressed: () => _openGooglePlaySubscriptionManagement(context),
              icon: const Icon(Icons.open_in_new, size: 18),
              label: const Text('Manage subscription'),
            ),
          ],
        ),
      ),
    );
  }
}
