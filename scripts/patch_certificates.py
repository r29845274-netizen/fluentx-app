from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding='utf-8')
    if new in text:
        print(f'{label}: already applied')
        return
    if old not in text:
        raise SystemExit(f'{label}: expected source block not found in {path}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')
    print(f'{label}: updated {path}')

# Add PDF generation/sharing dependencies.
pubspec = root / 'pubspec.yaml'
pub_text = pubspec.read_text(encoding='utf-8')
if '  pdf:' not in pub_text:
    marker = '  url_launcher: ^6.3.1\n'
    if marker not in pub_text:
        marker = '  timezone: ^0.9.4\n'
    if marker not in pub_text:
        raise SystemExit('certificate dependencies: dependency marker not found')
    pub_text = pub_text.replace(marker, marker + '  pdf: ^3.11.1\n  printing: ^5.13.4\n', 1)
    pubspec.write_text(pub_text, encoding='utf-8')

# Create Certificates screen.
screen = root / 'lib/features/certificates/presentation/screens/certificates_screen.dart'
screen.parent.mkdir(parents=True, exist_ok=True)
screen.write_text(r'''import 'package:flutter/material.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';
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
    return result.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList();
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  Future<void> _shareCertificate(Map<String, dynamic> row) async {
    final issued = row['issued'] == true;
    final code = (row['certificate_code'] ?? '').toString();
    if (!issued || code.isEmpty) return;

    final recipient = (row['recipient_name'] ?? 'FluentX Learner').toString();
    final title = (row['display_title'] ?? 'FluentX Completion Certificate').toString();
    final milestone = (row['milestone'] ?? '').toString();
    final issuedAt = DateTime.tryParse((row['issued_at'] ?? '').toString());
    final issuedLabel = issuedAt == null
        ? 'Issued by FluentX'
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
              pw.Text(milestone == 'MASTER' ? '60-Week FluentX Communication Mastery' : 'CEFR-aligned learning milestone: $milestone', style: const pw.TextStyle(fontSize: 13)),
              pw.SizedBox(height: 22),
              pw.Row(
                mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                children: [
                  pw.Text(issuedLabel, style: const pw.TextStyle(fontSize: 11)),
                  pw.Text('Credential ID: $code', style: pw.TextStyle(fontSize: 11, fontWeight: pw.FontWeight.bold)),
                ],
              ),
              pw.SizedBox(height: 10),
              pw.Text('FluentX course-completion credential. It is not an external accreditation or official CEFR examination certificate.', textAlign: pw.TextAlign.center, style: pw.TextStyle(fontSize: 8, color: PdfColors.grey700)),
            ],
          ),
        ),
      ),
    );

    await Printing.sharePdf(
      bytes: await doc.save(),
      filename: 'FluentX-$milestone-$code.pdf',
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
                              'Earn certificates as you complete your FluentX learning path.',
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
                                child: FilledButton.icon(
                                  onPressed: () => _shareCertificate(row),
                                  icon: const Icon(Icons.picture_as_pdf_outlined),
                                  label: const Text('Download / Share PDF'),
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
''', encoding='utf-8')
print(f'certificate screen: wrote {screen}')

# Route path.
routes = root / 'lib/routes/route_paths.dart'
replace_once(
    routes,
    "  static const String achievements = '/achievements';\n",
    "  static const String achievements = '/achievements';\n  static const String certificates = '/certificates';\n",
    'certificate route path',
)

# Router import + route.
router = root / 'lib/routes/app_router.dart'
router_text = router.read_text(encoding='utf-8')
if "../features/certificates/presentation/screens/certificates_screen.dart" not in router_text:
    marker = "import '../features/achievements/presentation/screens/achievements_screen.dart';\n"
    if marker not in router_text:
        raise SystemExit('certificate router import marker not found')
    router_text = router_text.replace(marker, marker + "import '../features/certificates/presentation/screens/certificates_screen.dart';\n", 1)

if 'path: RoutePaths.certificates' not in router_text:
    marker = r'''      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.achievements,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const AchievementsScreen(),
        ),
      ),
'''
    addition = marker + r'''      GoRoute(
        parentNavigatorKey: _rootNavigatorKey,
        path: RoutePaths.certificates,
        pageBuilder: (context, state) => buildPageWithTransition(
          context: context,
          state: state,
          child: const CertificatesScreen(),
        ),
      ),
'''
    if marker not in router_text:
        raise SystemExit('certificate router route marker not found')
    router_text = router_text.replace(marker, addition, 1)
router.write_text(router_text, encoding='utf-8')
print(f'certificate router: updated {router}')

# Profile entry.
profile = root / 'lib/features/profile/presentation/screens/profile_screen.dart'
profile_text = profile.read_text(encoding='utf-8')
if "label: 'Certificates'" not in profile_text:
    marker = r'''                      ProfileMenuTile(
                        icon: Icons.workspace_premium_outlined,
                        label: 'Achievements',
                        onTap: () => context.push(RoutePaths.achievements),
                      ),
                      const Divider(height: 1),
'''
    addition = marker + r'''                      ProfileMenuTile(
                        icon: Icons.verified_outlined,
                        label: 'Certificates',
                        onTap: () => context.push(RoutePaths.certificates),
                      ),
                      const Divider(height: 1),
'''
    if marker not in profile_text:
        raise SystemExit('certificate profile marker not found')
    profile.write_text(profile_text.replace(marker, addition, 1), encoding='utf-8')
    print(f'certificate profile entry: updated {profile}')

# Progress entry so users can discover it from the Progress tab too.
progress = root / 'lib/features/progress/presentation/screens/progress_screen.dart'
progress_text = progress.read_text(encoding='utf-8')
if "Text('Certificates'" not in progress_text:
    marker = r'''            AppCard(
              onTap: () => context.push(RoutePaths.achievements),
              child: Row(
                children: [
                  const Icon(Icons.workspace_premium_outlined, color: Color(0xFFD97706)),
                  const SizedBox(width: AppSpacing.md),
                  const Expanded(child: Text('View your badges and milestones')),
                  Icon(Icons.chevron_right, color: colorScheme.onSurfaceVariant),
                ],
              ),
            ),
'''
    addition = marker + r'''            const SizedBox(height: AppSpacing.xl),
            Text('Certificates', style: textTheme.headlineSmall),
            const SizedBox(height: AppSpacing.sm),
            AppCard(
              onTap: () => context.push(RoutePaths.certificates),
              child: Row(
                children: [
                  Icon(Icons.verified_outlined, color: colorScheme.primary),
                  const SizedBox(width: AppSpacing.md),
                  const Expanded(child: Text('View, download and share earned certificates')),
                  Icon(Icons.chevron_right, color: colorScheme.onSurfaceVariant),
                ],
              ),
            ),
'''
    if marker not in progress_text:
        raise SystemExit('certificate progress marker not found')
    progress.write_text(progress_text.replace(marker, addition, 1), encoding='utf-8')
    print(f'certificate progress entry: updated {progress}')

print('FluentX certificate experience applied.')
