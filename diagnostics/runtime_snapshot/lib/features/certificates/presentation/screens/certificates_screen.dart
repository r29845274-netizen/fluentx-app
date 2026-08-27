import 'package:flutter/material.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';
import 'package:purchases_flutter/purchases_flutter.dart';
import 'package:supabase_flutter/supabase_flutter.dart' as supabase;

import '../../../../core/constants/app_spacing.dart';
import '../../../../shared/widgets/widgets.dart';

class CertificatesScreen extends StatefulWidget {
  const CertificatesScreen({super.key});

  @override
  State<CertificatesScreen> createState() => _CertificatesScreenState();
}

class _CertificatesScreenState extends State<CertificatesScreen> {
  late Future<List<Map<String, dynamic>>> _future = _load();

  Future<List<Map<String, dynamic>>> _load() async {
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

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  Future<void> _shareCertificate(Map<String, dynamic> row) async {
    final issued = row['issued'] == true;
    final code = (row['certificate_code'] ?? '').toString();
    if (!issued || code.isEmpty) return;

    final recipient = (row['recipient_name'] ?? 'Fluent X Learner').toString();
    final title = (row['display_title'] ?? 'Fluent X Completion Certificate').toString();
    final milestone = (row['milestone'] ?? '').toString();
    final issuedAt = DateTime.tryParse((row['issued_at'] ?? '').toString());
    final issuedLabel = issuedAt == null
        ? 'Issued by Fluent X'
        : 'Issued ${issuedAt.day}/${issuedAt.month}/${issuedAt.year}';

    final doc = pw.Document();
    doc.addPage(
      pw.Page(
        pageFormat: PdfPageFormat.a4.landscape,
        margin: const pw.EdgeInsets.all(30),
        build: (context) => pw.Container(
          decoration: pw.BoxDecoration(
            border: pw.Border.all(color: PdfColor.fromHex('#7557F6'), width: 4),
          ),
          padding: const pw.EdgeInsets.all(34),
          child: pw.Column(
            mainAxisAlignment: pw.MainAxisAlignment.center,
            crossAxisAlignment: pw.CrossAxisAlignment.center,
            children: [
              pw.Text('FLUENTX', style: pw.TextStyle(fontSize: 23, fontWeight: pw.FontWeight.bold, color: PdfColor.fromHex('#7557F6'))),
              pw.SizedBox(height: 18),
              pw.Text('CERTIFICATE OF COMPLETION', style: pw.TextStyle(fontSize: 26, fontWeight: pw.FontWeight.bold)),
              pw.SizedBox(height: 25),
              pw.Text('This certifies that', style: const pw.TextStyle(fontSize: 14)),
              pw.SizedBox(height: 9),
              pw.Text(recipient, style: pw.TextStyle(fontSize: 32, fontWeight: pw.FontWeight.bold)),
              pw.SizedBox(height: 12),
              pw.Text('has successfully completed', style: const pw.TextStyle(fontSize: 14)),
              pw.SizedBox(height: 9),
              pw.Text(title, textAlign: pw.TextAlign.center, style: pw.TextStyle(fontSize: 19, fontWeight: pw.FontWeight.bold)),
              pw.SizedBox(height: 22),
              pw.Text(milestone == 'MASTER' ? '60-Week Fluent X Communication Mastery' : 'CEFR-aligned learning milestone: $milestone', style: const pw.TextStyle(fontSize: 13)),
              pw.SizedBox(height: 22),
              pw.Row(
                mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                children: [
                  pw.Text(issuedLabel, style: const pw.TextStyle(fontSize: 11)),
                  pw.Text('Credential ID: $code', style: pw.TextStyle(fontSize: 11, fontWeight: pw.FontWeight.bold)),
                ],
              ),
              pw.SizedBox(height: 10),
              pw.Text('Fluent X course-completion credential. It is not an external accreditation or official CEFR examination certificate.', textAlign: pw.TextAlign.center, style: pw.TextStyle(fontSize: 8, color: PdfColors.grey700)),
            ],
          ),
        ),
      ),
    );

    await Printing.sharePdf(
      bytes: await doc.save(),
      filename: 'Fluent X-$milestone-$code.pdf',
    );
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: const Text('My Certificates')),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<Map<String, dynamic>>>(
          future: _future,
          builder: (context, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return ListView(
                padding: const EdgeInsets.all(AppSpacing.xl),
                children: const [
                  ErrorStateWidget(message: 'We could not load your certificates right now.'),
                ],
              );
            }

            final rows = snapshot.data ?? <Map<String, dynamic>>[];
            return ListView(
              padding: const EdgeInsets.all(AppSpacing.base),
              children: [
                AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.workspace_premium_rounded, size: 34, color: colors.primary),
                          const SizedBox(width: AppSpacing.md),
                          Expanded(
                            child: Text(
                              'Earn certificates as you complete your Fluent X learning path.',
                              style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      Text(
                        'A certificate unlocks automatically when every required week in that level is completed. Finish all 60 weeks to unlock the Communication Mastery certificate.',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: AppSpacing.lg),
                if (rows.isEmpty)
                  const AppCard(child: Text('Your certificate milestones will appear here after your learning path is created.'))
                else
                  ...rows.map((row) {
                    final issued = row['issued'] == true;
                    final eligible = row['eligible'] == true;
                    final required = int.tryParse((row['required_weeks'] ?? 0).toString()) ?? 0;
                    final completed = int.tryParse((row['completed_weeks'] ?? 0).toString()) ?? 0;
                    final milestone = (row['milestone'] ?? '').toString();
                    final title = (row['display_title'] ?? milestone).toString();
                    final progress = required <= 0 ? 0.0 : (completed / required).clamp(0.0, 1.0);
                    final code = (row['certificate_code'] ?? '').toString();
                    final paidTier = (row['paid_tier'] ?? 'free').toString();
                    final isAnnual = paidTier == 'annual';
                    final isMonthly = paidTier == 'monthly';
                    final canDownload = issued && (isAnnual || (isMonthly && milestone != 'MASTER'));
                    final upgradeLabel = milestone == 'MASTER'
                        ? 'Annual Elite unlocks the Mastery PDF'
                        : 'Premium unlocks certificate PDF sharing';

                    return Padding(
                      padding: const EdgeInsets.only(bottom: AppSpacing.md),
                      child: AppCard(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                CircleAvatar(
                                  backgroundColor: issued ? colors.primary : colors.surfaceContainerHighest,
                                  child: Icon(
                                    issued ? Icons.verified_rounded : Icons.lock_outline_rounded,
                                    color: issued ? colors.onPrimary : colors.onSurfaceVariant,
                                  ),
                                ),
                                const SizedBox(width: AppSpacing.md),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
                                      const SizedBox(height: 3),
                                      Text(
                                        issued ? 'Certificate issued' : eligible ? 'Ready to issue' : '$completed of $required required weeks completed',
                                        style: Theme.of(context).textTheme.bodySmall,
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: AppSpacing.md),
                            LinearProgressIndicator(value: progress, minHeight: 8),
                            if (issued && code.isNotEmpty) ...[
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
                          ],
                        ),
                      ),
                    );
                  }),
              ],
            );
          },
        ),
      ),
    );
  }
}
