#!/usr/bin/env python3
from pathlib import Path

root = Path("fluentx_admin_secure")

# 1) Remove deleted/foreign Supabase defaults. Runtime values must come from dart-defines.
env_config = root / "lib/core/config/env_config.dart"
env_text = env_config.read_text()
env_text = env_text.replace(
    "defaultValue: 'https://ampcghxowbeocfqqnnvk.supabase.co',",
    "defaultValue: '',",
)
env_text = env_text.replace(
    "defaultValue: 'sb_publishable_TF58ThseSYp-CERYJklnbA_PL_F_rGo',",
    "defaultValue: '',",
)
if "appBuildNumber" not in env_text:
    env_text = env_text.replace(
        "static const String revenueCatApiKey = String.fromEnvironment('REVENUECAT_API_KEY');",
        "static const int appBuildNumber = int.fromEnvironment('APP_BUILD_NUMBER', defaultValue: 1);\n  static const String revenueCatApiKey = String.fromEnvironment('REVENUECAT_API_KEY');",
    )
env_config.write_text(env_text)

# 2) Keep Failure.uiMessage and ensure screens/widgets using it import the extension.
for path in (root / "lib").rglob("*.dart"):
    if path.name == "failures.dart":
        continue
    src = path.read_text()
    if ".uiMessage" in src and "package:fluentx/core/error/failures.dart" not in src and "core/error/failures.dart" not in src:
        path.write_text("import 'package:fluentx/core/error/failures.dart';\n" + src)

# 3) Map low-level connectivity exceptions to NetworkException.
datasource = root / "lib/features/authentication/data/datasources/auth_remote_datasource.dart"
ds = datasource.read_text()
helper = """Exception _mapAuthInfrastructureException(Object error) {
  final message = error.toString();
  final lower = message.toLowerCase();
  if (lower.contains('socketexception') ||
      lower.contains('failed host lookup') ||
      lower.contains('clientexception') ||
      lower.contains('network is unreachable') ||
      lower.contains('connection refused') ||
      lower.contains('connection reset') ||
      lower.contains('connection timed out')) {
    return const NetworkException(
      'Unable to connect to FluentX. Check your internet connection and try again.',
    );
  }
  return ServerException(message);
}

"""
if "_mapAuthInfrastructureException" not in ds:
    ds = ds.replace("abstract class AuthRemoteDataSource {", helper + "abstract class AuthRemoteDataSource {")
ds = ds.replace("throw ServerException(e.toString());", "throw _mapAuthInfrastructureException(e);")
datasource.write_text(ds)

# 4) Convert NetworkException to Failure.network at repository boundary.
repo_file = root / "lib/features/authentication/data/repositories/auth_repository_impl.dart"
rs = repo_file.read_text()
old = """    } on ServerException catch (e) {
      return left(Failure.server(message: e.message));
"""
new = """    } on NetworkException catch (e) {
      return left(Failure.network(message: e.message));
    } on ServerException catch (e) {
      return left(Failure.server(message: e.message));
"""
rs = rs.replace(old, new)
repo_file.write_text(rs)

# 5) Never expose server internals in UI; auth/network messages remain useful.
failures = root / "lib/core/error/failures.dart"
fs = failures.read_text()
fs = fs.replace(
    "ServerFailure(:final message) => message,",
    "ServerFailure() => 'Something went wrong. Please try again.',",
)
failures.write_text(fs)

# 6) Regression tests for the screenshot failure mode.
test = root / "test/core/error/failures_test.dart"
test.parent.mkdir(parents=True, exist_ok=True)
test.write_text("""import 'package:flutter_test/flutter_test.dart';
import 'package:fluentx/core/error/failures.dart';

void main() {
  test('network failure exposes only a friendly UI message', () {
    const failure = Failure.network(
      message: 'Unable to connect to FluentX. Check your internet connection and try again.',
    );
    expect(failure.uiMessage, contains('Unable to connect to FluentX'));
    expect(failure.uiMessage, isNot(contains('supabase.co')));
    expect(failure.uiMessage, isNot(contains('SocketException')));
  });

  test('server failure does not leak internal details', () {
    const failure = Failure.server(
      message: "ClientException with SocketException: Failed host lookup: bad.supabase.co",
    );
    expect(failure.uiMessage, 'Something went wrong. Please try again.');
    expect(failure.uiMessage, isNot(contains('supabase.co')));
  });
}
""")

old_ref = "ampcghxowbeocfqqnnvk"
for path in (root / "lib").rglob("*.dart"):
    if old_ref in path.read_text():
        raise SystemExit(f"stale Supabase project ref remains in {path}")

print("Supabase runtime connection + auth error UX fixes applied")


# 7) Add startup maintenance / force-update gate.
main_file = root / "lib/main.dart"
main_src = main_file.read_text()
needle = """    await Supabase.initialize(
      url: EnvConfig.supabaseUrl,
      anonKey: EnvConfig.supabaseAnonKey,
      authOptions: const FlutterAuthClientOptions(authFlowType: AuthFlowType.pkce),
    );
"""
insert = needle + """    try {
      final config = await Supabase.instance.client
          .from('app_config')
          .select('min_android_build, latest_android_build, force_update, maintenance_mode, support_email')
          .eq('id', true)
          .maybeSingle()
          .timeout(const Duration(seconds: 5));
      if (config != null && config['maintenance_mode'] == true) {
        runApp(const MaterialApp(home: Scaffold(body: SafeArea(child: Center(
          child: Padding(padding: EdgeInsets.all(24), child: Text(
            'FluentX is temporarily under maintenance. Please try again shortly.',
            textAlign: TextAlign.center,
          )),
        )))));
        return;
      }
      final minBuild = (config?['min_android_build'] as num?)?.toInt() ?? 1;
      if (config?['force_update'] == true && EnvConfig.appBuildNumber < minBuild) {
        runApp(const MaterialApp(home: Scaffold(body: SafeArea(child: Center(
          child: Padding(padding: EdgeInsets.all(24), child: Text(
            'A newer FluentX version is required. Please install the latest app build to continue.',
            textAlign: TextAlign.center,
          )),
        )))));
        return;
      }
    } catch (_) {
      // Remote app-config must not block startup if config lookup is unavailable.
    }
"""
if "min_android_build" not in main_src:
    main_src = main_src.replace(needle, insert)
main_file.write_text(main_src)

# 8) Upgrade Help & Support from FAQ-only to real Supabase ticket submission.
help_file = root / "lib/features/profile/presentation/screens/help_support_screen.dart"
help_file.write_text(r"""import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/network/supabase_provider.dart';
import '../../../../shared/widgets/widgets.dart';

class HelpSupportScreen extends ConsumerStatefulWidget {
  const HelpSupportScreen({super.key});

  @override
  ConsumerState<HelpSupportScreen> createState() => _HelpSupportScreenState();
}

class _HelpSupportScreenState extends ConsumerState<HelpSupportScreen> {
  static const _faqs = [
    ('How is my Communication DNA™ calculated?', 'Your practice activity is combined into Fluency, Vocabulary, Grammar, Pronunciation and Confidence scores.'),
    ('Why is my daily goal not updating?', 'Pull to refresh Home after saving a new goal. Make sure you are signed in and online.'),
    ('How do AI Practice sessions work?', 'Choose a scenario, speak or type your response, review inline corrections, then end the session for a summary.'),
    ('How do achievements unlock?', 'Badges unlock automatically when your streak, practice time, AI sessions or vocabulary milestones reach the required level.'),
  ];

  final _subject = TextEditingController();
  final _message = TextEditingController();
  bool _sending = false;
  String? _feedback;

  @override
  void dispose() {
    _subject.dispose();
    _message.dispose();
    super.dispose();
  }

  Future<void> _sendTicket() async {
    final subject = _subject.text.trim();
    final message = _message.text.trim();
    if (subject.length < 3 || message.length < 5) {
      setState(() => _feedback = 'Add a short subject and describe the issue.');
      return;
    }
    final client = ref.read(supabaseClientProvider);
    final user = client.auth.currentUser;
    if (user == null) {
      setState(() => _feedback = 'Please sign in again before contacting support.');
      return;
    }
    setState(() { _sending = true; _feedback = null; });
    try {
      await client.from('support_tickets').insert({
        'user_id': user.id,
        'subject': subject,
        'message': message,
      });
      _subject.clear();
      _message.clear();
      if (mounted) setState(() => _feedback = 'Support request sent. We will review it from the admin console.');
    } catch (_) {
      if (mounted) setState(() => _feedback = 'Could not send your request. Check your connection and try again.');
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Help & Support')),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.base),
        children: [
          AppCard(
            child: Row(
              children: [
                Icon(LucideIcons.lifeBuoy, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: AppSpacing.md),
                const Expanded(child: Text('Find quick answers or send a support request to the FluentX team.')),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.lg),
          Text('Contact support', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: AppSpacing.sm),
          AppCard(
            child: Column(
              children: [
                TextField(controller: _subject, maxLength: 120, decoration: const InputDecoration(labelText: 'Subject')),
                const SizedBox(height: AppSpacing.sm),
                TextField(controller: _message, minLines: 4, maxLines: 8, maxLength: 4000, decoration: const InputDecoration(labelText: 'Describe the issue')),
                const SizedBox(height: AppSpacing.sm),
                SizedBox(width: double.infinity, child: FilledButton.icon(
                  onPressed: _sending ? null : _sendTicket,
                  icon: _sending ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.send_outlined),
                  label: Text(_sending ? 'Sending…' : 'Send support request'),
                )),
                if (_feedback != null) ...[
                  const SizedBox(height: AppSpacing.sm),
                  Align(alignment: Alignment.centerLeft, child: Text(_feedback!)),
                ],
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.lg),
          Text('Frequently Asked Questions', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: AppSpacing.sm),
          for (final faq in _faqs)
            Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.sm),
              child: AppCard(
                child: ExpansionTile(
                  tilePadding: EdgeInsets.zero,
                  childrenPadding: const EdgeInsets.only(top: AppSpacing.sm),
                  title: Text(faq.$1),
                  children: [Align(alignment: Alignment.centerLeft, child: Text(faq.$2))],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
""")

print("Supabase runtime + PDF gap fixes applied")


# 9) Admin100 widget API compatibility.
admin_ui = root / "lib/features/admin/presentation/screens/admin_console_screen.dart"
ui = admin_ui.read_text()
for old, new in {
    "const EmptyStateWidget(message:'No users yet.')": "const EmptyStateWidget(title:'No users yet')",
    "const EmptyStateWidget(message:'No managed content yet.')": "const EmptyStateWidget(title:'No managed content yet')",
    "const EmptyStateWidget(message:'No support tickets.')": "const EmptyStateWidget(title:'No support tickets')",
    "const EmptyStateWidget(message:'No devices registered yet.')": "const EmptyStateWidget(title:'No devices registered yet')",
    "const EmptyStateWidget(message:'No promo codes yet.')": "const EmptyStateWidget(title:'No promo codes yet')",
    "const EmptyStateWidget(message:'No partners yet.')": "const EmptyStateWidget(title:'No partners yet')",
    "const EmptyStateWidget(message:'No moderation reports.')": "const EmptyStateWidget(title:'No moderation reports')",
    "const EmptyStateWidget(message:'No RevenueCat webhook events received yet.')": "const EmptyStateWidget(title:'No subscription events yet', message:'No RevenueCat webhook events received yet.')",
}.items():
    ui = ui.replace(old, new)
admin_ui.write_text(ui)
