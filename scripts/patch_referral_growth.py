from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')

screen = root / 'lib/features/profile/presentation/screens/referral_screen.dart'
screen.parent.mkdir(parents=True, exist_ok=True)
screen.write_text(r'''import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:url_launcher/url_launcher.dart';

class ReferralScreen extends StatefulWidget {
  const ReferralScreen({super.key});

  @override
  State<ReferralScreen> createState() => _ReferralScreenState();
}

class _ReferralScreenState extends State<ReferralScreen> {
  final _codeController = TextEditingController();
  Map<String, dynamic>? _dashboard;
  bool _loading = true;
  bool _redeeming = false;
  String? _error;

  SupabaseClient get _client => Supabase.instance.client;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _codeController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    if (mounted) setState(() { _loading = true; _error = null; });
    try {
      final data = await _client.rpc('get_my_referral_dashboard');
      if (!mounted) return;
      setState(() {
        _dashboard = data is Map ? Map<String, dynamic>.from(data) : <String, dynamic>{};
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() { _loading = false; _error = 'Referral program could not load right now.'; });
    }
  }

  String get _code => (_dashboard?['code'] ?? '').toString();

  String get _inviteText =>
      'I am improving my spoken English with FluentX and Maya AI. '
      'Join FluentX and use my invite code $_code to get 50 bonus XP. '
      'I also earn 100 XP when you join.';

  Future<void> _track(String event, String source) async {
    try {
      await _client.rpc('track_growth_event', params: {
        'p_event_name': event,
        'p_source': source,
        'p_metadata': {'referral_code': _code},
      });
    } catch (_) {}
  }

  Future<void> _copyCode() async {
    if (_code.isEmpty) return;
    await Clipboard.setData(ClipboardData(text: _code));
    await _track('referral_code_copied', 'referral_screen');
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Invite code copied.')));
  }

  Future<void> _copyInvite() async {
    if (_code.isEmpty) return;
    await Clipboard.setData(ClipboardData(text: _inviteText));
    await _track('referral_message_copied', 'referral_screen');
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Invite message copied.')));
  }

  Future<void> _shareWhatsApp() async {
    if (_code.isEmpty) return;
    await _track('referral_share_clicked', 'whatsapp');
    final uri = Uri.parse('https://wa.me/?text=${Uri.encodeComponent(_inviteText)}');
    final launched = await launchUrl(uri, mode: LaunchMode.externalApplication);
    if (!launched && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('WhatsApp could not be opened. Copy the invite message instead.')));
    }
  }

  Future<void> _redeem() async {
    final code = _codeController.text.trim();
    if (code.isEmpty || _redeeming) return;
    setState(() { _redeeming = true; _error = null; });
    try {
      final data = await _client.rpc('redeem_referral_code', params: {'p_code': code});
      final map = data is Map ? Map<String, dynamic>.from(data) : <String, dynamic>{};
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text((map['message'] ?? 'Referral applied.').toString())));
      _codeController.clear();
      await _load();
    } on PostgrestException catch (e) {
      if (!mounted) return;
      setState(() => _error = e.message.contains('not found') ? 'That invite code was not found.' : e.message);
    } catch (_) {
      if (!mounted) return;
      setState(() => _error = 'Could not apply this invite code.');
    } finally {
      if (mounted) setState(() => _redeeming = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    if (_loading) return const Scaffold(appBar: _ReferralAppBar(), body: Center(child: CircularProgressIndicator()));

    final referrals = int.tryParse((_dashboard?['successful_referrals'] ?? 0).toString()) ?? 0;
    final earnedXp = int.tryParse((_dashboard?['earned_xp'] ?? 0).toString()) ?? 0;

    return Scaffold(
      appBar: const _ReferralAppBar(),
      body: SafeArea(
        top: false,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                gradient: LinearGradient(colors: [colors.primaryContainer, colors.secondaryContainer]),
                borderRadius: BorderRadius.circular(22),
              ),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('Invite friends. Grow together.', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900)),
                const SizedBox(height: 6),
                const Text('Your friend gets 50 XP. You get 100 XP after a successful referral.'),
                const SizedBox(height: 16),
                Row(children: [
                  Expanded(child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
                    decoration: BoxDecoration(color: colors.surface.withValues(alpha: .82), borderRadius: BorderRadius.circular(15)),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      const Text('YOUR CODE', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800)),
                      const SizedBox(height: 3),
                      Text(_code, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900, letterSpacing: 1.4)),
                    ]),
                  )),
                  const SizedBox(width: 8),
                  IconButton.filled(onPressed: _copyCode, icon: const Icon(Icons.copy_rounded), tooltip: 'Copy code'),
                ]),
                const SizedBox(height: 12),
                Row(children: [
                  Expanded(child: FilledButton.icon(onPressed: _shareWhatsApp, icon: const Icon(Icons.chat_rounded), label: const Text('Share on WhatsApp'))),
                  const SizedBox(width: 8),
                  Expanded(child: OutlinedButton.icon(onPressed: _copyInvite, icon: const Icon(Icons.content_copy_rounded), label: const Text('Copy Invite'))),
                ]),
              ]),
            ),
            const SizedBox(height: 16),
            Row(children: [
              Expanded(child: _StatCard(icon: Icons.group_add_rounded, value: '$referrals', label: 'Friends joined')),
              const SizedBox(width: 10),
              Expanded(child: _StatCard(icon: Icons.bolt_rounded, value: '$earnedXp XP', label: 'Referral rewards')),
            ]),
            const SizedBox(height: 22),
            Text('Have an invite code?', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 8),
            TextField(
              controller: _codeController,
              textCapitalization: TextCapitalization.characters,
              decoration: const InputDecoration(border: OutlineInputBorder(), labelText: 'Enter FluentX invite code', prefixIcon: Icon(Icons.card_giftcard_rounded)),
            ),
            const SizedBox(height: 10),
            FilledButton(
              onPressed: _redeeming ? null : _redeem,
              child: Text(_redeeming ? 'Applying…' : 'Apply Invite Code'),
            ),
            if (_error != null) ...[
              const SizedBox(height: 10),
              Text(_error!, style: TextStyle(color: colors.error), textAlign: TextAlign.center),
            ],
            const SizedBox(height: 24),
            const _HowItWorks(),
          ],
        ),
      ),
    );
  }
}

class _ReferralAppBar extends StatelessWidget implements PreferredSizeWidget {
  const _ReferralAppBar();
  @override Size get preferredSize => const Size.fromHeight(kToolbarHeight);
  @override Widget build(BuildContext context) => AppBar(title: const Text('Invite & Earn'));
}

class _StatCard extends StatelessWidget {
  const _StatCard({required this.icon, required this.value, required this.label});
  final IconData icon;
  final String value;
  final String label;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(15),
    decoration: BoxDecoration(color: Theme.of(context).colorScheme.surfaceContainerHighest, borderRadius: BorderRadius.circular(16)),
    child: Column(children: [
      Icon(icon, color: Theme.of(context).colorScheme.primary),
      const SizedBox(height: 7),
      Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
      const SizedBox(height: 2),
      Text(label, textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodySmall),
    ]),
  );
}

class _HowItWorks extends StatelessWidget {
  const _HowItWorks();
  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Text('How it works', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
    const SizedBox(height: 10),
    const _Step(number: '1', text: 'Share your FluentX invite code.'),
    const _Step(number: '2', text: 'Your friend signs in and applies the code.'),
    const _Step(number: '3', text: 'They receive 50 XP and you receive 100 XP.'),
  ]);
}

class _Step extends StatelessWidget {
  const _Step({required this.number, required this.text});
  final String number;
  final String text;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 10),
    child: Row(children: [
      CircleAvatar(radius: 15, child: Text(number, style: const TextStyle(fontWeight: FontWeight.w900))),
      const SizedBox(width: 10),
      Expanded(child: Text(text)),
    ]),
  );
}
''', encoding='utf-8')

routes = root / 'lib/routes/route_paths.dart'
text = routes.read_text(encoding='utf-8')
if "static const String referral" not in text:
    text = text.replace("  static const String dailyGoals = '/daily-goals';", "  static const String dailyGoals = '/daily-goals';\n  static const String referral = '/invite';", 1)
routes.write_text(text, encoding='utf-8')

router = root / 'lib/routes/app_router.dart'
text = router.read_text(encoding='utf-8')
if "referral_screen.dart" not in text:
    text = text.replace("import '../features/profile/presentation/screens/profile_screen.dart';", "import '../features/profile/presentation/screens/profile_screen.dart';\nimport '../features/profile/presentation/screens/referral_screen.dart';", 1)
if "path: RoutePaths.referral" not in text:
    marker = "      GoRoute(\n        parentNavigatorKey: _rootNavigatorKey,\n        path: RoutePaths.helpSupport,"
    pos = text.find(marker)
    if pos < 0: raise SystemExit('Help Support route marker not found')
    block = """      GoRoute(\n        parentNavigatorKey: _rootNavigatorKey,\n        path: RoutePaths.referral,\n        pageBuilder: (context, state) => buildPageWithTransition(\n          context: context,\n          state: state,\n          child: const ReferralScreen(),\n        ),\n      ),\n"""
    text = text[:pos] + block + text[pos:]
router.write_text(text, encoding='utf-8')

profile = root / 'lib/features/profile/presentation/screens/profile_screen.dart'
text = profile.read_text(encoding='utf-8')
if "label: 'Invite & Earn'" not in text:
    marker = "                      ProfileMenuTile(\n                        icon: Icons.gps_fixed,\n                        label: 'Daily Goals',"
    pos = text.find(marker)
    if pos < 0: raise SystemExit('Daily Goals profile marker not found')
    block = """                      ProfileMenuTile(\n                        icon: Icons.group_add_outlined,\n                        label: 'Invite & Earn',\n                        onTap: () => context.push(RoutePaths.referral),\n                      ),\n                      const Divider(height: 1),\n"""
    text = text[:pos] + block + text[pos:]
profile.write_text(text, encoding='utf-8')

print('Referral growth UI applied: invite dashboard, WhatsApp share, rewards, redemption and profile route.')
