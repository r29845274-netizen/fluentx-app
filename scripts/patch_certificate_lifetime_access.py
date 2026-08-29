from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
cert = root / 'lib/features/certificates/presentation/screens/certificates_screen.dart'
if not cert.exists():
    raise SystemExit('Certificates screen not found')

text = cert.read_text(encoding='utf-8')

# Free users: final MASTER certificate PDF is a one-time lifetime purchase.
# Monthly/Annual premium users: final certificate PDF is included at no extra cost.
# RevenueCat source of truth:
#   premium entitlement              -> active monthly/yearly subscriber
#   certificate_lifetime entitlement -> one-time non-consumable purchase
# Recommended Google Play product id: fluentx_final_certificate_lifetime
# Recommended India price: INR 499 one-time (actual localized price comes from Play).

old_state = "  late Future<List<Map<String, dynamic>>> _future = _load();\n"
new_state = old_state + "  bool _purchasingCertificate = false;\n"
if 'bool _purchasingCertificate = false;' not in text:
    if old_state not in text:
        raise SystemExit('certificate state marker not found')
    text = text.replace(old_state, new_state, 1)

old_load = r'''  Future<List<Map<String, dynamic>>> _load() async {
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
new_load = r'''  Package? _certificateLifetimePackage(Offerings offerings) {
    final current = offerings.current;
    if (current == null) return null;
    for (final package in current.availablePackages) {
      final key = '${package.identifier} ${package.storeProduct.identifier}'.toLowerCase();
      if (package.packageType == PackageType.lifetime ||
          (key.contains('certificate') && key.contains('lifetime'))) {
        return package;
      }
    }
    return null;
  }

  Future<List<Map<String, dynamic>>> _load() async {
    final result = await supabase.Supabase.instance.client.rpc('get_my_certificate_status');
    if (result is! List) return <Map<String, dynamic>>[];

    var paidTier = 'free';
    var hasLifetimeCertificate = false;
    var certificatePrice = '₹499';
    try {
      final info = await Purchases.getCustomerInfo();
      final entitlement = info.entitlements.active['premium'];
      if (entitlement != null) {
        paidTier = entitlement.productPlanIdentifier?.toLowerCase() == 'annual'
            ? 'annual'
            : 'monthly';
      }
      hasLifetimeCertificate =
          info.entitlements.active['certificate_lifetime'] != null;

      final offerings = await Purchases.getOfferings();
      final package = _certificateLifetimePackage(offerings);
      if (package != null) certificatePrice = package.storeProduct.priceString;
    } catch (_) {
      // Billing can be unavailable in local/dev builds. Eligibility still loads.
    }

    return result.whereType<Map>().map((e) {
      final row = Map<String, dynamic>.from(e);
      row['paid_tier'] = paidTier;
      row['certificate_lifetime'] = hasLifetimeCertificate;
      row['certificate_price'] = certificatePrice;
      return row;
    }).toList();
  }

  Future<void> _purchaseFinalCertificate() async {
    if (_purchasingCertificate) return;
    setState(() => _purchasingCertificate = true);
    try {
      final offerings = await Purchases.getOfferings();
      final package = _certificateLifetimePackage(offerings);
      if (package == null) {
        throw Exception('Final certificate purchase is not available yet.');
      }

      final result = await Purchases.purchase(PurchaseParams.package(package));
      final unlocked =
          result.customerInfo.entitlements.active['certificate_lifetime'] != null;
      if (!unlocked) {
        throw Exception('Purchase completed but lifetime access is not active yet.');
      }

      await _refresh();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Final certificate unlocked for lifetime.')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
        );
      }
    } finally {
      if (mounted) setState(() => _purchasingCertificate = false);
    }
  }
'''
if new_load not in text:
    if old_load not in text:
        raise SystemExit('certificate membership load marker not found')
    text = text.replace(old_load, new_load, 1)

old_vars = r'''                    final paidTier = (row['paid_tier'] ?? 'free').toString();
                    final isAnnual = paidTier == 'annual';
                    final isMonthly = paidTier == 'monthly';
                    final canDownload = issued && (isAnnual || (isMonthly && milestone != 'MASTER'));
                    final upgradeLabel = milestone == 'MASTER'
                        ? 'Annual Elite unlocks the Mastery PDF'
                        : 'Premium unlocks certificate PDF sharing';
'''
new_vars = r'''                    final paidTier = (row['paid_tier'] ?? 'free').toString();
                    final isAnnual = paidTier == 'annual';
                    final isMonthly = paidTier == 'monthly';
                    final isSubscriber = isAnnual || isMonthly;
                    final hasLifetimeCertificate = row['certificate_lifetime'] == true;
                    final certificatePrice = (row['certificate_price'] ?? '₹499').toString();
                    final isMaster = milestone == 'MASTER';
                    final canDownload = issued &&
                        (!isMaster || isSubscriber || hasLifetimeCertificate);
'''
if new_vars not in text:
    if old_vars not in text:
        raise SystemExit('certificate access variables marker not found')
    text = text.replace(old_vars, new_vars, 1)

old_button = r'''                              SizedBox(
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
'''
new_button = r'''                              SizedBox(
                                width: double.infinity,
                                child: canDownload
                                    ? FilledButton.icon(
                                        onPressed: () => _shareCertificate(row),
                                        icon: const Icon(Icons.picture_as_pdf_outlined),
                                        label: Text(
                                          isMaster && isSubscriber
                                              ? 'Included · Download / Share PDF'
                                              : isMaster && hasLifetimeCertificate
                                                  ? 'Lifetime · Download / Share PDF'
                                                  : 'Download / Share PDF',
                                        ),
                                      )
                                    : isMaster
                                        ? FilledButton.icon(
                                            onPressed: _purchasingCertificate
                                                ? null
                                                : _purchaseFinalCertificate,
                                            icon: const Icon(Icons.workspace_premium_outlined),
                                            label: Text(
                                              _purchasingCertificate
                                                  ? 'Processing…'
                                                  : 'Unlock Final Certificate · $certificatePrice one-time',
                                            ),
                                          )
                                        : const SizedBox.shrink(),
                              ),
                              if (isMaster && !isSubscriber) ...[
                                const SizedBox(height: AppSpacing.sm),
                                Text(
                                  hasLifetimeCertificate
                                      ? 'Lifetime certificate access is active on this account.'
                                      : 'One-time payment. Lifetime access after purchase. Monthly and Yearly subscribers get the final certificate at no extra cost.',
                                  style: Theme.of(context).textTheme.bodySmall,
                                  textAlign: TextAlign.center,
                                ),
                              ],
'''
if new_button not in text:
    if old_button not in text:
        raise SystemExit('certificate paid button marker not found')
    text = text.replace(old_button, new_button, 1)

text = text.replace(
    'A certificate unlocks automatically when every required week in that level is completed. Finish all 60 weeks to unlock the Communication Mastery certificate.',
    'Certificates unlock automatically as you complete the learning path. Finish all 60 weeks to earn the final Communication Mastery certificate. Monthly and Yearly subscribers get the final PDF included; Free members can unlock it once for lifetime access.',
)

cert.write_text(text, encoding='utf-8')
print(f'certificate lifetime access: updated {cert}')

# Update visible subscription value copy so both paid plans clearly include certificates.
premium = root / 'lib/features/premium/presentation/screens/premium_screen.dart'
if premium.exists():
    p = premium.read_text(encoding='utf-8')
    p = p.replace(
        "? 'ELITE ID • Mastery Certificate • Gold profile identity'",
        "? 'ELITE ID • Final Certificate included • Gold profile identity'",
    )
    p = p.replace(
        ": 'PRO ID • Level certificates • Premium profile identity',",
        ": 'PRO ID • Final Certificate included • Premium profile identity',",
    )
    premium.write_text(p, encoding='utf-8')

card = root / 'lib/features/premium/presentation/widgets/membership_identity_card.dart'
if card.exists():
    c = card.read_text(encoding='utf-8')
    c = c.replace(
        "? 'Elite identity • Mastery Certificate • all Pro benefits'",
        "? 'Elite identity • final certificate included • all Pro benefits'",
    )
    c = c.replace(
        ": 'Pro identity • level certificate downloads • premium access'",
        ": 'Pro identity • final certificate included • premium access'",
    )
    card.write_text(c, encoding='utf-8')

print('Fluent X final certificate lifetime model applied.')
