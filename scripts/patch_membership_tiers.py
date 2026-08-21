from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')

# -----------------------------------------------------------------------------
# FluentX membership identity and paid-tier presentation.
#
# Stable identity: Supabase owns an 8-character member_key that never changes.
# Visible membership code changes with verified RevenueCat state:
#   Free    -> FX-XXXXXXXX
#   Monthly -> FXM-XXXXXXXX  (FluentX Pro)
#   Annual  -> FXY-XXXXXXXX  (FluentX Elite)
#
# Important: the prefix/badge is presentation only. Premium access still comes
# from the active RevenueCat `premium` entitlement; users cannot unlock access
# by editing an ID string.
# -----------------------------------------------------------------------------

provider = root / 'lib/features/premium/application/providers/membership_identity_provider.dart'
provider.parent.mkdir(parents=True, exist_ok=True)
provider.write_text(r'''import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:purchases_flutter/purchases_flutter.dart';
import 'package:supabase_flutter/supabase_flutter.dart' as supabase;

enum FluentXMembershipTier { free, monthly, annual }

class FluentXMemberIdentity {
  const FluentXMemberIdentity({
    required this.memberKey,
    required this.joinedAt,
    required this.tier,
  });

  final String memberKey;
  final DateTime? joinedAt;
  final FluentXMembershipTier tier;

  bool get isPaid => tier != FluentXMembershipTier.free;
  bool get isAnnual => tier == FluentXMembershipTier.annual;

  String get memberId => switch (tier) {
        FluentXMembershipTier.free => 'FX-$memberKey',
        FluentXMembershipTier.monthly => 'FXM-$memberKey',
        FluentXMembershipTier.annual => 'FXY-$memberKey',
      };

  String get tierName => switch (tier) {
        FluentXMembershipTier.free => 'FluentX Member',
        FluentXMembershipTier.monthly => 'FluentX Pro',
        FluentXMembershipTier.annual => 'FluentX Elite',
      };

  String get badgeLabel => switch (tier) {
        FluentXMembershipTier.free => 'MEMBER',
        FluentXMembershipTier.monthly => 'PRO',
        FluentXMembershipTier.annual => 'ELITE',
      };
}

final memberIdentityProvider = FutureProvider<FluentXMemberIdentity>((ref) async {
  final client = supabase.Supabase.instance.client;
  String memberKey = 'MEMBER';
  DateTime? joinedAt;

  final rawIdentity = await client.rpc('get_my_member_identity');
  if (rawIdentity is List && rawIdentity.isNotEmpty && rawIdentity.first is Map) {
    final row = Map<String, dynamic>.from(rawIdentity.first as Map);
    memberKey = (row['member_key'] ?? memberKey).toString().toUpperCase();
    joinedAt = DateTime.tryParse((row['joined_at'] ?? '').toString());
  } else if (rawIdentity is Map) {
    final row = Map<String, dynamic>.from(rawIdentity);
    memberKey = (row['member_key'] ?? memberKey).toString().toUpperCase();
    joinedAt = DateTime.tryParse((row['joined_at'] ?? '').toString());
  }

  var tier = FluentXMembershipTier.free;
  try {
    final info = await Purchases.getCustomerInfo();
    final entitlement = info.entitlements.active['premium'];
    if (entitlement != null) {
      // Google Play base-plan IDs are locked as `monthly` and `annual`.
      // RevenueCat exposes the Google base plan as productPlanIdentifier.
      final plan = entitlement.productPlanIdentifier?.toLowerCase();
      tier = plan == 'annual'
          ? FluentXMembershipTier.annual
          : FluentXMembershipTier.monthly;
    }
  } catch (_) {
    // Billing may be intentionally unavailable in local/dev builds.
  }

  return FluentXMemberIdentity(
    memberKey: memberKey,
    joinedAt: joinedAt,
    tier: tier,
  );
});
''', encoding='utf-8')
print(f'membership provider: wrote {provider}')

widget = root / 'lib/features/premium/presentation/widgets/membership_identity_card.dart'
widget.parent.mkdir(parents=True, exist_ok=True)
widget.write_text(r'''import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/app_radius.dart';
import '../../../../core/constants/app_spacing.dart';
import '../../../../shared/widgets/widgets.dart';
import '../../application/providers/membership_identity_provider.dart';

class MembershipIdentityCard extends ConsumerWidget {
  const MembershipIdentityCard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final identityAsync = ref.watch(memberIdentityProvider);
    final colors = Theme.of(context).colorScheme;

    return identityAsync.when(
      loading: () => const LoadingCardSkeleton(lines: 2),
      error: (_, __) => const SizedBox.shrink(),
      data: (identity) {
        final isElite = identity.tier == FluentXMembershipTier.annual;
        final isPro = identity.tier == FluentXMembershipTier.monthly;
        final accent = isElite
            ? const Color(0xFFD97706)
            : isPro
                ? colors.primary
                : colors.onSurfaceVariant;

        return Container(
          width: double.infinity,
          padding: const EdgeInsets.all(AppSpacing.base),
          decoration: BoxDecoration(
            borderRadius: AppRadius.lgAll,
            gradient: isElite
                ? const LinearGradient(
                    colors: [Color(0xFFFFF7D6), Color(0xFFFFE7A3)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  )
                : isPro
                    ? LinearGradient(
                        colors: [
                          colors.primaryContainer,
                          colors.secondaryContainer,
                        ],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      )
                    : null,
            color: (!isElite && !isPro) ? colors.surfaceContainerLow : null,
            border: Border.all(color: accent.withValues(alpha: .35)),
          ),
          child: Row(
            children: [
              Container(
                width: 46,
                height: 46,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: accent.withValues(alpha: .14),
                  borderRadius: AppRadius.mdAll,
                ),
                child: Icon(
                  isElite ? Icons.auto_awesome_rounded : isPro ? Icons.workspace_premium_rounded : Icons.person_outline_rounded,
                  color: accent,
                ),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            identity.tierName,
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
                          decoration: BoxDecoration(
                            color: accent.withValues(alpha: .14),
                            borderRadius: AppRadius.fullAll,
                          ),
                          child: Text(
                            identity.badgeLabel,
                            style: TextStyle(color: accent, fontSize: 11, fontWeight: FontWeight.w900),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Member ID  ${identity.memberId}',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            fontWeight: FontWeight.w800,
                            letterSpacing: .5,
                          ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      isElite
                          ? 'Elite identity • Mastery Certificate • all Pro benefits'
                          : isPro
                              ? 'Pro identity • level certificate downloads • premium access'
                              : 'Upgrade to Pro or Elite to transform your member identity.',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
''', encoding='utf-8')
print(f'membership identity card: wrote {widget}')

# Profile: show identity directly under the normal profile header.
profile = root / 'lib/features/profile/presentation/screens/profile_screen.dart'
text = profile.read_text(encoding='utf-8')
identity_import = "import '../../../premium/presentation/widgets/membership_identity_card.dart';\n"
if identity_import not in text:
    marker = "import '../../../premium/application/providers/purchase_providers.dart';\n"
    if marker not in text:
        raise SystemExit('membership profile import marker not found')
    text = text.replace(marker, marker + identity_import, 1)

if 'const MembershipIdentityCard()' not in text:
    marker = r'''                ProfileHeader(
                  fullName: user.fullName ?? user.email.split('@').first,
                  email: user.email,
                  avatarUrl: user.avatarUrl,
                  levelProgress: levelProgress,
                  isPremium: isPremium,
                ),
                const SizedBox(height: AppSpacing.xl),
'''
    replacement = r'''                ProfileHeader(
                  fullName: user.fullName ?? user.email.split('@').first,
                  email: user.email,
                  avatarUrl: user.avatarUrl,
                  levelProgress: levelProgress,
                  isPremium: isPremium,
                ),
                const SizedBox(height: AppSpacing.base),
                const MembershipIdentityCard(),
                const SizedBox(height: AppSpacing.xl),
'''
    if marker not in text:
        raise SystemExit('membership profile card marker not found')
    text = text.replace(marker, replacement, 1)
profile.write_text(text, encoding='utf-8')
print(f'membership profile: updated {profile}')

# Premium paywall: make the visible value difference between plans explicit.
premium = root / 'lib/features/premium/presentation/screens/premium_screen.dart'
text = premium.read_text(encoding='utf-8')
price_marker = "                  Text(package.priceString, style: Theme.of(context).textTheme.bodySmall),\n"
if "package.period == 'yearly'\n                      ? 'ELITE ID" not in text:
    extra = price_marker + r'''                  const SizedBox(height: 3),
                  Text(
                    package.period == 'yearly'
                        ? 'ELITE ID • Mastery Certificate • Gold profile identity'
                        : 'PRO ID • Level certificates • Premium profile identity',
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                          fontWeight: FontWeight.w600,
                        ),
                  ),
'''
    if price_marker not in text:
        raise SystemExit('premium plan value marker not found')
    text = text.replace(price_marker, extra, 1)
premium.write_text(text, encoding='utf-8')
print(f'membership paywall: updated {premium}')

# Certificates: RevenueCat-verified tier controls downloadable paid perks.
cert = root / 'lib/features/certificates/presentation/screens/certificates_screen.dart'
text = cert.read_text(encoding='utf-8')
if "package:purchases_flutter/purchases_flutter.dart" not in text:
    marker = "import 'package:printing/printing.dart';\n"
    if marker not in text:
        raise SystemExit('certificate RevenueCat import marker not found')
    text = text.replace(marker, marker + "import 'package:purchases_flutter/purchases_flutter.dart';\n", 1)

old_load = r'''  Future<List<Map<String, dynamic>>> _load() async {
    final result = await supabase.Supabase.instance.client.rpc('get_my_certificate_status');
    if (result is! List) return <Map<String, dynamic>>[];
    return result.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList();
  }
'''
new_load = r'''  Future<List<Map<String, dynamic>>> _load() async {
    final result = await supabase.Supabase.instance.client.rpc('get_my_certificate_status');
    if (result is! List) return <Map<String, dynamic>>[];

    var paidTier = 'free';
    try {
      final info = await Purchases.getCustomerInfo();
      final entitlement = info.entitlements.active['premium'];
      if (entitlement != null) {
        paidTier = entitlement.productPlanIdentifier?.toLowerCase() == 'annual'
            ? 'annual'
            : 'monthly';
      }
    } catch (_) {}

    return result.whereType<Map>().map((e) {
      final row = Map<String, dynamic>.from(e);
      row['paid_tier'] = paidTier;
      return row;
    }).toList();
  }
'''
if new_load not in text:
    if old_load not in text:
        raise SystemExit('certificate tier load marker not found')
    text = text.replace(old_load, new_load, 1)

old_code = r'''                    final code = (row['certificate_code'] ?? '').toString();

                    return Padding(
'''
new_code = r'''                    final code = (row['certificate_code'] ?? '').toString();
                    final paidTier = (row['paid_tier'] ?? 'free').toString();
                    final isAnnual = paidTier == 'annual';
                    final isMonthly = paidTier == 'monthly';
                    final canDownload = issued && (isAnnual || (isMonthly && milestone != 'MASTER'));
                    final upgradeLabel = milestone == 'MASTER'
                        ? 'Annual Elite unlocks the Mastery PDF'
                        : 'Premium unlocks certificate PDF sharing';

                    return Padding(
'''
if new_code not in text:
    if old_code not in text:
        raise SystemExit('certificate tier variables marker not found')
    text = text.replace(old_code, new_code, 1)

old_button = r'''                            if (issued && code.isNotEmpty) ...[
                              const SizedBox(height: AppSpacing.md),
                              Text('Credential ID: $code', style: Theme.of(context).textTheme.labelMedium),
                              const SizedBox(height: AppSpacing.sm),
                              SizedBox(
                                width: double.infinity,
                                child: FilledButton.icon(
                                  onPressed: () => _shareCertificate(row),
                                  icon: const Icon(Icons.picture_as_pdf_outlined),
                                  label: const Text('Download / Share PDF'),
                                ),
                              ),
                            ],
'''
new_button = r'''                            if (issued && code.isNotEmpty) ...[
                              const SizedBox(height: AppSpacing.md),
                              Text('Credential ID: $code', style: Theme.of(context).textTheme.labelMedium),
                              const SizedBox(height: AppSpacing.sm),
                              SizedBox(
                                width: double.infinity,
                                child: canDownload
                                    ? FilledButton.icon(
                                        onPressed: () => _shareCertificate(row),
                                        icon: const Icon(Icons.picture_as_pdf_outlined),
                                        label: Text(isAnnual ? 'ELITE · Download / Share PDF' : 'PRO · Download / Share PDF'),
                                      )
                                    : OutlinedButton.icon(
                                        onPressed: null,
                                        icon: const Icon(Icons.lock_outline_rounded),
                                        label: Text(upgradeLabel),
                                      ),
                              ),
                            ],
'''
if new_button not in text:
    if old_button not in text:
        raise SystemExit('certificate gated download marker not found')
    text = text.replace(old_button, new_button, 1)

cert.write_text(text, encoding='utf-8')
print(f'membership certificates: updated {cert}')

print('FluentX membership tier experience applied.')
