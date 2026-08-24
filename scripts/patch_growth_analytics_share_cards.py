from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')

# -----------------------------------------------------------------------------
# 1) Dependencies for local PNG card generation + native Android share sheet.
# -----------------------------------------------------------------------------
pubspec = root / 'pubspec.yaml'
text = pubspec.read_text(encoding='utf-8')
if 'share_plus:' not in text:
    text = text.replace('  url_launcher: ^6.3.1\n', '  url_launcher: ^6.3.1\n  share_plus: ^10.1.4\n  path_provider: ^2.1.5\n', 1)
pubspec.write_text(text, encoding='utf-8')

# -----------------------------------------------------------------------------
# 2) Reusable share-card screen.
# -----------------------------------------------------------------------------
screen = root / 'lib/features/progress/presentation/screens/share_progress_card_screen.dart'
screen.parent.mkdir(parents=True, exist_ok=True)
screen.write_text(r'''import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class ShareProgressCardScreen extends StatefulWidget {
  const ShareProgressCardScreen({super.key, this.mode = 'progress'});

  final String mode;

  @override
  State<ShareProgressCardScreen> createState() => _ShareProgressCardScreenState();
}

class _ShareProgressCardScreenState extends State<ShareProgressCardScreen> {
  final GlobalKey _cardKey = GlobalKey();
  Map<String, dynamic> _stats = const {};
  bool _loading = true;
  bool _sharing = false;
  String? _error;

  SupabaseClient get _client => Supabase.instance.client;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await _client.rpc('get_my_share_stats');
      if (!mounted) return;
      setState(() {
        _stats = data is Map ? Map<String, dynamic>.from(data) : <String, dynamic>{};
        _loading = false;
      });
      await _track('share_card_viewed');
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = 'Your share card could not load right now.';
      });
    }
  }

  int _int(String key, [int fallback = 0]) => int.tryParse((_stats[key] ?? fallback).toString()) ?? fallback;
  String _str(String key, [String fallback = '']) => (_stats[key] ?? fallback).toString();

  Future<void> _track(String event) async {
    try {
      await _client.rpc('track_growth_event', params: {
        'p_event_name': event,
        'p_source': 'share_card',
        'p_metadata': {'card_type': widget.mode},
      });
    } catch (_) {}
  }

  Future<File?> _renderPng() async {
    final context = _cardKey.currentContext;
    if (context == null) return null;
    final boundary = context.findRenderObject() as RenderRepaintBoundary?;
    if (boundary == null) return null;
    final image = await boundary.toImage(pixelRatio: 2.5);
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    if (bytes == null) return null;
    final dir = await getTemporaryDirectory();
    final file = File('${dir.path}/fluentx_${widget.mode}_card.png');
    await file.writeAsBytes(bytes.buffer.asUint8List(), flush: true);
    return file;
  }

  Future<void> _share() async {
    if (_sharing) return;
    setState(() => _sharing = true);
    try {
      final file = await _renderPng();
      if (file == null) throw StateError('Card image could not be generated.');
      final level = _str('cefr_level', 'A1');
      final week = _int('current_week', 1);
      final streak = _int('streak_days');
      final text = widget.mode == 'achievement'
          ? 'I am building my English speaking habit with FluentX — $streak day streak!'
          : 'My FluentX English progress: $level • Week $week • $streak day streak. Practicing with Maya AI.';
      await Share.shareXFiles([XFile(file.path)], text: text, subject: 'My FluentX English Progress');
      await _track('share_card_shared');
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Could not open the share sheet. Please try again.')));
    } finally {
      if (mounted) setState(() => _sharing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    return Scaffold(
      appBar: AppBar(title: Text(widget.mode == 'achievement' ? 'Share Achievement' : 'Share Progress')),
      body: SafeArea(
        top: false,
        child: ListView(
          padding: const EdgeInsets.all(18),
          children: [
            if (_error != null) ...[
              Text(_error!, textAlign: TextAlign.center),
              const SizedBox(height: 16),
            ],
            Center(
              child: RepaintBoundary(
                key: _cardKey,
                child: _ProgressShareCard(stats: _stats, mode: widget.mode),
              ),
            ),
            const SizedBox(height: 20),
            FilledButton.icon(
              onPressed: _sharing || _error != null ? null : _share,
              icon: const Icon(Icons.ios_share_rounded),
              label: Text(_sharing ? 'Preparing card…' : 'Share This Card'),
            ),
            const SizedBox(height: 8),
            Text(
              'Your card contains learning progress only — no email, phone number or private conversation text.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}

class _ProgressShareCard extends StatelessWidget {
  const _ProgressShareCard({required this.stats, required this.mode});
  final Map<String, dynamic> stats;
  final String mode;

  int _int(String key, [int fallback = 0]) => int.tryParse((stats[key] ?? fallback).toString()) ?? fallback;
  String _str(String key, [String fallback = '']) => (stats[key] ?? fallback).toString();

  @override
  Widget build(BuildContext context) {
    const purple = Color(0xFF7557F6);
    final streak = _int('streak_days');
    final xp = _int('xp_earned');
    final activeDays = _int('total_active_days');
    final week = _int('current_week', 1);
    final level = _str('cefr_level', 'A1');
    final mastery = _int('weekly_mastery_streak');
    final referrals = _int('successful_referrals');

    return Container(
      width: 360,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFF7F4FF), Color(0xFFE9E2FF)],
        ),
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: purple.withValues(alpha: .18)),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Container(
            width: 44,
            height: 44,
            alignment: Alignment.center,
            decoration: const BoxDecoration(color: purple, shape: BoxShape.circle),
            child: const Text('FX', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900)),
          ),
          const SizedBox(width: 12),
          const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('FluentX', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900)),
            Text('AI English Speaking Coach', style: TextStyle(fontSize: 12)),
          ])),
        ]),
        const SizedBox(height: 24),
        Text(
          mode == 'achievement' ? 'My English Learning Achievement' : 'My English Progress',
          style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w900),
        ),
        const SizedBox(height: 7),
        Text(
          mode == 'achievement'
              ? '$streak day learning streak 🔥'
              : '$level level • Week $week of 60',
          style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: purple),
        ),
        const SizedBox(height: 20),
        Row(children: [
          Expanded(child: _CardStat(value: '$streak', label: 'Day Streak', icon: Icons.local_fire_department_rounded)),
          const SizedBox(width: 8),
          Expanded(child: _CardStat(value: '$xp', label: 'XP', icon: Icons.bolt_rounded)),
          const SizedBox(width: 8),
          Expanded(child: _CardStat(value: '$activeDays', label: 'Active Days', icon: Icons.calendar_month_rounded)),
        ]),
        const SizedBox(height: 9),
        Row(children: [
          Expanded(child: _MiniLine(icon: Icons.workspace_premium_rounded, label: '$mastery weekly mastery streak')),
          const SizedBox(width: 8),
          Expanded(child: _MiniLine(icon: Icons.group_add_rounded, label: '$referrals friends joined')),
        ]),
        const SizedBox(height: 22),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(color: Colors.white.withValues(alpha: .72), borderRadius: BorderRadius.circular(16)),
          child: const Text(
            'Practicing spoken English with Maya AI ✨',
            textAlign: TextAlign.center,
            style: TextStyle(fontWeight: FontWeight.w800),
          ),
        ),
      ]),
    );
  }
}

class _CardStat extends StatelessWidget {
  const _CardStat({required this.value, required this.label, required this.icon});
  final String value;
  final String label;
  final IconData icon;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 7),
    decoration: BoxDecoration(color: Colors.white.withValues(alpha: .74), borderRadius: BorderRadius.circular(15)),
    child: Column(children: [
      Icon(icon, size: 20, color: const Color(0xFF7557F6)),
      const SizedBox(height: 5),
      Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
      Text(label, textAlign: TextAlign.center, style: const TextStyle(fontSize: 9.5)),
    ]),
  );
}

class _MiniLine extends StatelessWidget {
  const _MiniLine({required this.icon, required this.label});
  final IconData icon;
  final String label;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(10),
    decoration: BoxDecoration(color: Colors.white.withValues(alpha: .5), borderRadius: BorderRadius.circular(13)),
    child: Row(children: [
      Icon(icon, size: 17, color: const Color(0xFF7557F6)),
      const SizedBox(width: 6),
      Expanded(child: Text(label, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700))),
    ]),
  );
}
''', encoding='utf-8')

# -----------------------------------------------------------------------------
# 3) Route wiring.
# -----------------------------------------------------------------------------
routes = root / 'lib/routes/route_paths.dart'
text = routes.read_text(encoding='utf-8')
if 'shareProgress' not in text:
    text = text.replace("  static const String communicationDna = '/communication-dna';", "  static const String communicationDna = '/communication-dna';\n  static const String shareProgress = '/share-progress';", 1)
routes.write_text(text, encoding='utf-8')

router = root / 'lib/routes/app_router.dart'
text = router.read_text(encoding='utf-8')
if 'share_progress_card_screen.dart' not in text:
    text = text.replace("import '../features/progress/presentation/screens/progress_screen.dart';", "import '../features/progress/presentation/screens/progress_screen.dart';\nimport '../features/progress/presentation/screens/share_progress_card_screen.dart';", 1)
if 'path: RoutePaths.shareProgress' not in text:
    marker = "      GoRoute(\n        parentNavigatorKey: _rootNavigatorKey,\n        path: RoutePaths.communicationDna,"
    pos = text.find(marker)
    if pos < 0:
        raise SystemExit('Communication DNA route marker not found')
    block = """      GoRoute(\n        parentNavigatorKey: _rootNavigatorKey,\n        path: RoutePaths.shareProgress,\n        pageBuilder: (context, state) => buildPageWithTransition(\n          context: context,\n          state: state,\n          child: ShareProgressCardScreen(\n            mode: state.uri.queryParameters['mode'] ?? 'progress',\n          ),\n        ),\n      ),\n"""
    text = text[:pos] + block + text[pos:]
router.write_text(text, encoding='utf-8')

# -----------------------------------------------------------------------------
# 4) Progress screen share CTA.
# -----------------------------------------------------------------------------
progress = root / 'lib/features/progress/presentation/screens/progress_screen.dart'
text = progress.read_text(encoding='utf-8')
if "Share My Progress" not in text:
    marker = "            Text('Communication DNA™', style: textTheme.headlineSmall),"
    block = """            Container(\n              padding: const EdgeInsets.all(16),\n              decoration: BoxDecoration(\n                color: colorScheme.primaryContainer.withValues(alpha: .48),\n                borderRadius: BorderRadius.circular(18),\n              ),\n              child: Row(children: [\n                const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [\n                  Text('Share your progress', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 17)),\n                  SizedBox(height: 3),\n                  Text('Create a clean FluentX progress card for WhatsApp or social media.'),\n                ])),\n                FilledButton.tonalIcon(\n                  onPressed: () => context.push('${RoutePaths.shareProgress}?mode=progress'),\n                  icon: const Icon(Icons.ios_share_rounded),\n                  label: const Text('Share'),\n                ),\n              ]),\n            ),\n            const SizedBox(height: AppSpacing.xl),\n"""
    text = text.replace(marker, block + marker, 1)
progress.write_text(text, encoding='utf-8')

# -----------------------------------------------------------------------------
# 5) Achievements screen share CTA.
# -----------------------------------------------------------------------------
ach = root / 'lib/features/achievements/presentation/screens/achievements_screen.dart'
text = ach.read_text(encoding='utf-8')
if "Share Achievement" not in text:
    if "package:go_router/go_router.dart" not in text:
        text = text.replace("import 'package:flutter_riverpod/flutter_riverpod.dart';", "import 'package:flutter_riverpod/flutter_riverpod.dart';\nimport 'package:go_router/go_router.dart';", 1)
    if "route_paths.dart" not in text:
        text = text.replace("import '../../../../core/router/onboarding_status_provider.dart';", "import '../../../../core/router/onboarding_status_provider.dart';\nimport '../../../../routes/route_paths.dart';", 1)
    marker = "        const SizedBox(height: AppSpacing.lg),\n        GridView.builder("
    block = """        FilledButton.icon(\n          onPressed: () => context.push('${RoutePaths.shareProgress}?mode=achievement'),\n          icon: const Icon(Icons.ios_share_rounded),\n          label: const Text('Share Achievement'),\n        ),\n        const SizedBox(height: AppSpacing.lg),\n        GridView.builder("""
    text = text.replace(marker, block, 1)
ach.write_text(text, encoding='utf-8')

# -----------------------------------------------------------------------------
# 6) Referral conversion numbers on existing Invite & Earn screen.
# -----------------------------------------------------------------------------
referral = root / 'lib/features/profile/presentation/screens/referral_screen.dart'
if referral.exists():
    text = referral.read_text(encoding='utf-8')
    if "Share → Join conversion" not in text:
        marker = "            const SizedBox(height: 22),\n            Text('Have an invite code?'"
        block = r'''            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(color: colors.surfaceContainerHighest, borderRadius: BorderRadius.circular(16)),
              child: Row(children: [
                Expanded(child: _ReferralMetric(label: 'Share attempts', value: '${_dashboard?['share_attempts'] ?? 0}')),
                Expanded(child: _ReferralMetric(label: 'Message copies', value: '${_dashboard?['copy_attempts'] ?? 0}')),
                Expanded(child: _ReferralMetric(label: 'Share → Join conversion', value: '${_dashboard?['conversion_rate_percent'] ?? 0}%')),
              ]),
            ),
'''
        text = text.replace(marker, block + marker, 1)
        insert = r'''
class _ReferralMetric extends StatelessWidget {
  const _ReferralMetric({required this.label, required this.value});
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) => Column(children: [
    Text(value, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w900)),
    const SizedBox(height: 2),
    Text(label, textAlign: TextAlign.center, style: Theme.of(context).textTheme.labelSmall),
  ]);
}

'''
        idx = text.find('class _HowItWorks')
        if idx >= 0:
            text = text[:idx] + insert + text[idx:]
    referral.write_text(text, encoding='utf-8')

# -----------------------------------------------------------------------------
# 7) App-open growth signal after authentication becomes available.
# -----------------------------------------------------------------------------
main = root / 'lib/main.dart'
text = main.read_text(encoding='utf-8')
if 'Future<void> _trackGrowthAppOpen()' not in text:
    helper = r'''
Future<void> _trackGrowthAppOpen() async {
  if (Supabase.instance.client.auth.currentUser == null) return;
  try {
    await Supabase.instance.client.rpc('track_growth_event', params: {
      'p_event_name': 'app_open',
      'p_source': 'app',
      'p_metadata': {'platform': 'android'},
    });
  } catch (_) {}
}

'''
    idx = text.find('Future<void> main() async {')
    text = text[:idx] + helper + text[idx:]
if 'await _trackGrowthAppOpen();' not in text:
    text = text.replace('  _watchBillingIdentity();\n', '  _watchBillingIdentity();\n  await _trackGrowthAppOpen();\n', 1)
main.write_text(text, encoding='utf-8')

print('Growth analytics UI applied: app-open tracking, referral conversion metrics, and PNG progress/achievement sharing.')
