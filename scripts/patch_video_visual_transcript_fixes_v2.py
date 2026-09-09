from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
if not (root / 'lib').exists():
    raise SystemExit(f'Flutter source not found: {root}')

changed = []

def save(path: Path, before: str, after: str) -> None:
    if before != after:
        path.write_text(after)
        changed.append(str(path.relative_to(root)))

# ---------------------------------------------------------------------------
# 1) Onboarding: the recording showed a RenderFlex overflow beside
#    "Start Level Check" on a narrow phone. Keep the two-button layout on
#    wider screens, but stack the controls on narrow widths.
# ---------------------------------------------------------------------------
onboarding = root / 'lib/features/onboarding/presentation/screens/onboarding_screen.dart'
if onboarding.exists():
    before = onboarding.read_text()
    code = before
    old = '''            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: onBack,
                    child: const Text('Back'),
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: PrimaryButton(
                    label: 'Start Level Check',
                    isLoading: isLoading,
                    isEnabled: selectedGoal != null,
                    onPressed: selectedGoal == null ? null : onNext,
                  ),
                ),
              ],
            ),'''
    new = '''            LayoutBuilder(
              builder: (context, constraints) {
                final start = PrimaryButton(
                  label: 'Start Level Check',
                  isLoading: isLoading,
                  isEnabled: selectedGoal != null,
                  onPressed: selectedGoal == null ? null : onNext,
                );
                final back = OutlinedButton(
                  onPressed: onBack,
                  child: const Text('Back'),
                );
                if (constraints.maxWidth < 390) {
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      SizedBox(width: double.infinity, child: start),
                      const SizedBox(height: AppSpacing.sm),
                      SizedBox(width: double.infinity, child: back),
                    ],
                  );
                }
                return Row(
                  children: [
                    Expanded(child: back),
                    const SizedBox(width: AppSpacing.sm),
                    Expanded(flex: 2, child: start),
                  ],
                );
              },
            ),'''
    if old in code:
        code = code.replace(old, new, 1)
    elif "constraints.maxWidth < 390" not in code:
        raise SystemExit('Could not locate Start Level Check button row for overflow fix.')
    save(onboarding, before, code)

# ---------------------------------------------------------------------------
# 2) Maya: make the offline fallback intent-aware instead of replying with
#    unrelated generic coaching. The real AI remains remote-first; this only
#    improves the truthful guided fallback when the Edge Function is offline.
# ---------------------------------------------------------------------------
maya = root / 'lib/features/ai_practice/presentation/screens/ai_practice_hub_screen.dart'
if maya.exists():
    before = maya.read_text()
    code = before
    start = code.find('  String _localPracticeReply(String message) {')
    end = code.find('  int _limitForTier(String tier)', start)
    if start < 0 or end < 0:
        raise SystemExit('Could not locate Maya local reply helper.')

    local_reply = r'''  String _localPracticeReply(String message) {
    final clean = message.trim();
    final lower = clean.toLowerCase();
    final words = clean.split(RegExp(r'\s+')).where((w) => w.isNotEmpty).length;

    final asksIdentity = lower.contains('who are you') ||
        lower.contains('what are you') ||
        lower.contains("what's your name") ||
        lower.contains('what is your name') ||
        lower.contains('your name?');
    if (asksIdentity) {
      return 'I’m Maya, your Fluent X English speaking partner. I can have conversations with you, help you say things naturally in English, and gently correct mistakes. What would you like to talk about?';
    }
    if (lower.contains('where are you from')) {
      return 'I’m a virtual AI tutor inside Fluent X, so I don’t have a physical hometown. You can practice by telling me where you’re from in one natural English sentence.';
    }
    if (lower.contains('what can you do') || lower.contains('how can you help') || lower.contains('help me with english')) {
      return 'I can practice everyday conversation, work, travel, interviews and pronunciation with you. I can also suggest more natural English and explain mistakes. Tell me what you want to practice.';
    }
    if (lower.contains('my name is') || lower.startsWith("i'm ") || lower.startsWith('i am ')) {
      return 'Nice to meet you! 😊 Thanks for introducing yourself. How are you today, and what would you like to talk about?';
    }
    if (lower.contains('how are you')) {
      return 'I’m doing well, thank you 😊 How are you today? You can answer naturally, for example: “I’m good, and I’m practicing English today.”';
    }
    if (lower == 'hi' || lower == 'hii' || lower == 'hlo' ||
        lower == 'hello' || lower == 'hey' || lower.startsWith('hlo maya') ||
        lower.startsWith('hello maya') || lower.startsWith('hi maya')) {
      return 'Hi! 😊 I’m Maya. What would you like to talk about today?';
    }
    if (lower.contains("what's up") || lower.contains('whats up') ||
        lower.contains('what s up') || lower.contains('what’s up') ||
        lower.contains('whats ap') || lower.contains("what's ap") || lower.contains('what’s ap')) {
      return 'Not much — I’m ready to practice English with you 😊 “What’s up?” is the natural phrase. What are you doing right now?';
    }
    if (lower.contains('thank')) {
      return 'You’re welcome! 😊 What would you like to talk about next?';
    }
    if (lower.contains('bye') || lower.contains('goodbye') || lower.contains('see you')) {
      return 'See you soon! Keep practicing a little English every day. 😊';
    }
    if (clean.endsWith('?')) {
      return 'I understood your question: “$clean” Live AI is reconnecting, so I don’t want to invent a specific answer while offline. You can keep practicing this question, or retry when Maya is online for a direct answer.';
    }
    if (words < 5) {
      return 'I heard you: “$clean” Add one more detail and I’ll continue from exactly what you said.';
    }
    return 'I understood: “$clean” Tell me one more detail about that, and I’ll keep the conversation focused on your topic.';
  }

'''
    code = code[:start] + local_reply + code[end:]

    # Offline guided turns are still real learning activity. Record them for
    # XP/streak/daily-goal progress, while keeping AI billable time at zero.
    local_block = re.compile(
        r"(if \(_sessionId!\.startsWith\('local-'\)\) \{.*?_scrollDown\(\);\n)(\s*if \(_speakerOn\) await _speak\(reply, 'en-IN', 'encouraging'\);)",
        re.S,
    )
    code, n_local_activity = local_block.subn(
        r"\1      await _recordMayaActivity();\n\2",
        code,
        count=1,
    )
    if n_local_activity == 0 and "await _recordMayaActivity();\n      if (_speakerOn) await _speak(reply, 'en-IN', 'encouraging');" not in code:
        raise SystemExit('Could not wire Maya offline activity tracking.')

    save(maya, before, code)

# ---------------------------------------------------------------------------
# 3) Authentication: make password sign-in the stable default, align the
#    visible password rule with the backend's 10-character minimum, prevent
#    confirmation links from pointing at localhost, and replace raw OTP
#    backend wording with a user-facing message.
# ---------------------------------------------------------------------------
login = root / 'lib/features/authentication/presentation/screens/login_screen.dart'
if login.exists():
    before = login.read_text()
    code = before.replace('  bool _useOtp = true;', '  bool _useOtp = false;', 1)
    save(login, before, code)

signup = root / 'lib/features/authentication/presentation/screens/signup_screen.dart'
if signup.exists():
    before = signup.read_text()
    code = before
    old_validator = """                    validator: Validators.password,\n                    helperText: 'At least 8 characters, 1 uppercase, 1 number',"""
    new_validator = r"""                    validator: (value) {
                      final password = value ?? '';
                      if (password.length < 10) return 'Use at least 10 characters';
                      if (!RegExp(r'[A-Z]').hasMatch(password)) return 'Add at least 1 uppercase letter';
                      if (!RegExp(r'[0-9]').hasMatch(password)) return 'Add at least 1 number';
                      return null;
                    },
                    helperText: 'At least 10 characters, 1 uppercase, 1 number',"""
    if old_validator in code:
        code = code.replace(old_validator, new_validator, 1)
    else:
        # The older video patch may have changed only the helper text. Replace
        # the validator/helper pair based on its structural location.
        code, n = re.subn(
            r"\s{20}validator: Validators\.password,\n\s{20}helperText: 'At least \d+ characters, 1 uppercase, 1 number',",
            new_validator,
            code,
            count=1,
        )
        if n == 0 and "Use at least 10 characters" not in code:
            raise SystemExit('Could not align signup password validation to 10 characters.')
    save(signup, before, code)

auth_ds = root / 'lib/features/authentication/data/datasources/auth_remote_datasource.dart'
if auth_ds.exists():
    before = auth_ds.read_text()
    code = before
    signup_call = """      final response = await _client.auth.signUp(\n        email: email,\n        password: password,\n        data: {'full_name': fullName},\n      );"""
    signup_call_fixed = """      final response = await _client.auth.signUp(\n        email: email,\n        password: password,\n        data: {'full_name': fullName},\n        emailRedirectTo: _oauthRedirectUri,\n      );"""
    if signup_call in code:
        code = code.replace(signup_call, signup_call_fixed, 1)
    elif 'emailRedirectTo: _oauthRedirectUri' not in code:
        raise SystemExit('Could not add signup email deep-link redirect.')

    otp_func = re.compile(
        r"  @override\n  Future<void> sendLoginOtp\(String email\) async \{.*?\n  \}\n\n  @override\n  Future<AppUser> verifyEmailOtp",
        re.S,
    )
    otp_replacement = r'''  @override
  Future<void> sendLoginOtp(String email) async {
    try {
      await _client.auth.signInWithOtp(
        email: email,
        shouldCreateUser: false,
      );
    } on supabase.AuthException catch (e) {
      final message = e.message.toLowerCase();
      if (message.contains('signups not allowed') ||
          message.contains('user not found') ||
          message.contains('no user')) {
        throw const AuthException(
          'No account found with this email. Create an account first or sign in with your password.',
        );
      }
      throw AuthException(e.message);
    } catch (e) {
      throw ServerException(e.toString());
    }
  }

  @override
  Future<AppUser> verifyEmailOtp'''
    code, n_otp = otp_func.subn(otp_replacement, code, count=1)
    if n_otp == 0 and 'No account found with this email.' not in code:
        raise SystemExit('Could not replace raw OTP login error handling.')
    save(auth_ds, before, code)

otp_screen = root / 'lib/features/authentication/presentation/screens/otp_verification_screen.dart'
if otp_screen.exists():
    before = otp_screen.read_text()
    code = before
    old_copy = """              Text(\n                'We sent a 6-digit email OTP to ${widget.email}',\n                style: Theme.of(context).textTheme.bodyLarge?.copyWith(\n                      color: colorScheme.onSurfaceVariant,\n                    ),\n              ),"""
    new_copy = """              Text(\n                widget.isSignup\n                    ? 'We sent a verification email to ${widget.email}. Enter the 6-digit code if your email shows one. If it has a Confirm email address button instead, tap that button and return to Fluent X.'\n                    : 'We sent a 6-digit email OTP to ${widget.email}',\n                style: Theme.of(context).textTheme.bodyLarge?.copyWith(\n                      color: colorScheme.onSurfaceVariant,\n                    ),\n              ),"""
    if old_copy in code:
        code = code.replace(old_copy, new_copy, 1)
    elif 'If it has a Confirm email address button instead' not in code:
        raise SystemExit('Could not add signup verification-link guidance.')
    save(otp_screen, before, code)

# ---------------------------------------------------------------------------
# 4) Premium: RevenueCat/Google Play can be unavailable in a sideloaded debug
#    APK. Never hide the plans behind a spinner/error. Show an honest plan
#    preview (without fake prices or a fake purchase button) and let users retry.
#    Also make subscription status fall back to Free instead of hanging forever.
# ---------------------------------------------------------------------------
purchase_ds = root / 'lib/features/premium/data/datasources/purchase_remote_datasource.dart'
if purchase_ds.exists():
    before = purchase_ds.read_text()
    code = before
    old_status = """    Purchases.getCustomerInfo().then((info) => controller.add(_mapCustomerInfo(info)));\n    return controller.stream;"""
    new_status = """    Purchases.getCustomerInfo()\n        .timeout(const Duration(seconds: 8))\n        .then((info) {\n          if (!controller.isClosed) controller.add(_mapCustomerInfo(info));\n        })\n        .catchError((_) {\n          if (!controller.isClosed) controller.add(SubscriptionStatus.free);\n        });\n    return controller.stream;"""
    if old_status in code:
        code = code.replace(old_status, new_status, 1)
    elif '.timeout(const Duration(seconds: 8))' not in code:
        raise SystemExit('Could not bound RevenueCat customer-info startup wait.')
    code = code.replace(
        'final offerings = await Purchases.getOfferings();',
        'final offerings = await Purchases.getOfferings().timeout(const Duration(seconds: 8));',
        1,
    )
    save(purchase_ds, before, code)

premium = root / 'lib/features/premium/presentation/screens/premium_screen.dart'
if premium.exists():
    before = premium.read_text()
    code = before

    # Remove the full-screen timeout branch; package-level fallback below keeps
    # the rest of the premium screen visible.
    code, removed = re.subn(
        r"\n    if \(subscriptionAsync\.isLoading && _billingTimedOut\) \{.*?\n    \}\n\n    ref\.listen\(purchaseControllerProvider,",
        "\n    ref.listen(purchaseControllerProvider,",
        code,
        count=1,
        flags=re.S,
    )
    if removed == 0 and 'Google Play plans are taking too long to load' in code:
        raise SystemExit('Could not remove full-screen Premium billing timeout.')

    old_empty = """                    if (packages.isEmpty) {\n                      return const EmptyStateWidget(\n                        title: 'Plans unavailable right now',\n                        message: 'Please check back shortly.',\n                      );\n                    }"""
    new_empty = """                    if (packages.isEmpty) {\n                      return _BillingPlanPreview(onRetry: _retryBilling);\n                    }"""
    if old_empty in code:
        code = code.replace(old_empty, new_empty, 1)

    code = code.replace(
        "                  loading: () => const LoadingCardSkeleton(),\n                  error: (_, __) => ErrorStateWidget(\n                    onRetry: () => ref.invalidate(premiumPackagesProvider),\n                  ),",
        "                  loading: () => _billingTimedOut\n                      ? _BillingPlanPreview(onRetry: _retryBilling)\n                      : const LoadingCardSkeleton(),\n                  error: (_, __) => _BillingPlanPreview(onRetry: _retryBilling),",
        1,
    )

    preview = r'''
class _BillingPlanPreview extends StatelessWidget {
  const _BillingPlanPreview({required this.onRetry});
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;

    Widget plan(String title, String identity, {bool best = false}) {
      return Container(
        width: double.infinity,
        margin: const EdgeInsets.only(bottom: AppSpacing.sm),
        padding: const EdgeInsets.all(AppSpacing.base),
        decoration: BoxDecoration(
          borderRadius: AppRadius.lgAll,
          border: Border.all(color: colors.outlineVariant),
          color: colors.surfaceContainerLowest,
        ),
        child: Row(children: [
          Icon(Icons.workspace_premium_outlined, color: colors.primary),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(title, style: Theme.of(context).textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w800)),
              const SizedBox(height: 2),
              const Text('Price loads securely from Google Play'),
              const SizedBox(height: 2),
              Text(identity, style: Theme.of(context).textTheme.labelSmall?.copyWith(color: colors.onSurfaceVariant)),
            ]),
          ),
          if (best)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.sm, vertical: 2),
              decoration: BoxDecoration(
                color: const Color(0xFF16A34A).withValues(alpha: .12),
                borderRadius: AppRadius.fullAll,
              ),
              child: const Text('Best Value', style: TextStyle(color: Color(0xFF16A34A), fontSize: 11, fontWeight: FontWeight.w700)),
            ),
        ]),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        plan('Monthly', 'PRO ID • Final Certificate included'),
        plan('Yearly', 'ELITE ID • Final Certificate included', best: true),
        const SizedBox(height: AppSpacing.xs),
        Text(
          'Google Play billing is not connected yet on this installation. No purchase will be attempted until live products load.',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(color: colors.onSurfaceVariant),
        ),
        const SizedBox(height: AppSpacing.sm),
        OutlinedButton.icon(
          onPressed: onRetry,
          icon: const Icon(Icons.refresh_rounded),
          label: const Text('Retry Google Play plans'),
        ),
      ],
    );
  }
}

'''
    marker = 'class _PlanTile extends StatelessWidget {'
    if 'class _BillingPlanPreview extends StatelessWidget' not in code:
        pos = code.find(marker)
        if pos < 0:
            raise SystemExit('Could not insert Premium billing plan preview widget.')
        code = code[:pos] + preview + code[pos:]

    if '_BillingPlanPreview(onRetry: _retryBilling)' not in code:
        raise SystemExit('Premium preview fallback was not wired.')
    save(premium, before, code)

# ---------------------------------------------------------------------------
# 5) Vocabulary completion -> actual learning activity. The recording showed
#    a completed lesson while Home/Profile remained at 0 XP and 0 streak.
#    Record one completed session through the existing secure RPC and refresh
#    Home/Achievements. No fake client-side XP totals are created.
# ---------------------------------------------------------------------------
vocab = root / 'lib/features/vocabulary/presentation/screens/vocabulary_screen.dart'
if vocab.exists():
    before = vocab.read_text()
    code = before
    if "package:supabase_flutter/supabase_flutter.dart" not in code:
        code = code.replace(
            "import 'package:flutter_riverpod/flutter_riverpod.dart';\n",
            "import 'package:flutter_riverpod/flutter_riverpod.dart';\nimport 'package:supabase_flutter/supabase_flutter.dart';\n",
            1,
        )
    if "../../../home/application/providers/home_providers.dart" not in code:
        code = code.replace(
            "import '../../application/providers/vocabulary_providers.dart';\n",
            "import '../../application/providers/vocabulary_providers.dart';\nimport '../../../home/application/providers/home_providers.dart';\nimport '../../../achievements/application/providers/achievements_providers.dart';\n",
            1,
        )

    session_re = re.compile(
        r"class _SessionComplete extends StatelessWidget \{.*?\n\}\n\s*$",
        re.S,
    )
    session_new = r'''class _SessionComplete extends ConsumerStatefulWidget {
  const _SessionComplete({required this.reviewedCount});

  final int reviewedCount;

  @override
  ConsumerState<_SessionComplete> createState() => _SessionCompleteState();
}

class _SessionCompleteState extends ConsumerState<_SessionComplete> {
  bool _recorded = false;

  @override
  void initState() {
    super.initState();
    Future<void>.microtask(_recordCompletion);
  }

  Future<void> _recordCompletion() async {
    if (_recorded) return;
    _recorded = true;
    try {
      await Supabase.instance.client.rpc(
        'record_my_learning_activity',
        params: {'p_source': 'vocabulary_review_session'},
      );
      if (!mounted) return;
      ref.invalidate(homeSummaryProvider);
      ref.invalidate(achievementStatsProvider);
    } catch (_) {
      // Keep the completed-session UI usable if progress sync is temporarily
      // unavailable. A later server refresh can reconcile progress.
    }
  }

  @override
  Widget build(BuildContext context) {
    final reviewedCount = widget.reviewedCount;
    return EmptyStateWidget(
      title: 'Session complete! 🎉',
      message: 'You reviewed $reviewedCount word${reviewedCount == 1 ? '' : 's'} today.',
      icon: Icons.celebration,
    );
  }
}
'''
    code, n_session = session_re.subn(session_new, code, count=1)
    if n_session == 0 and 'vocabulary_review_session' not in code:
        raise SystemExit('Could not wire vocabulary completion progress sync.')
    save(vocab, before, code)

print('Full video + transcript fixes v2 applied.')
print('Changed files:')
for item in changed:
    print(' -', item)
