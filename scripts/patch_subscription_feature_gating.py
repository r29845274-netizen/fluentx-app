from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')


def ensure_import(path: Path, marker: str, new_import: str, label: str) -> None:
    text = path.read_text(encoding='utf-8')
    if new_import in text:
        return
    if marker not in text:
        raise SystemExit(f'{label}: import marker not found in {path}')
    path.write_text(text.replace(marker, marker + new_import, 1), encoding='utf-8')


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding='utf-8')
    if new in text:
        print(f'{label}: already applied')
        return
    if old not in text:
        raise SystemExit(f'{label}: expected block not found in {path}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')
    print(f'{label}: updated {path}')


# -----------------------------------------------------------------------------
# Tier rules
# Free    : core learning path and standard learning tools.
# Monthly : FluentX Pro — AI English Coach + level certificate PDF sharing.
# Annual  : FluentX Elite — all Pro benefits + AI Interview Coach,
#           Communication DNA advanced insights + Mastery certificate PDF.
# RevenueCat remains the source of truth. This patch only gates presentation /
# feature entry based on verified active entitlement + Google base-plan ID.
# -----------------------------------------------------------------------------

# AI Practice: paid (Monthly + Annual).
ai = root / 'lib/features/ai_practice/presentation/screens/ai_practice_hub_screen.dart'
ensure_import(
    ai,
    "import 'package:flutter_riverpod/flutter_riverpod.dart';\n",
    "import 'package:go_router/go_router.dart';\n",
    'AI practice go_router import',
)
ensure_import(
    ai,
    "import '../../../../shared/widgets/widgets.dart';\n",
    "import '../../../../routes/route_paths.dart';\nimport '../../../premium/application/providers/membership_identity_provider.dart';\n",
    'AI practice membership imports',
)
old = """  @override
  Widget build(BuildContext context) {
    final sessionState = ref.watch(aiPracticeSessionControllerProvider);

    if (_activeScenario != null && sessionState.summary != null) {
"""
new = """  @override
  Widget build(BuildContext context) {
    final identityAsync = ref.watch(memberIdentityProvider);
    if (identityAsync.isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    final identity = identityAsync.valueOrNull;
    if (identity == null || identity.tier == FluentXMembershipTier.free) {
      return Scaffold(
        appBar: AppBar(title: const Text('AI English Coach')),
        body: SafeArea(
          child: Center(
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.xl),
              child: AppCard(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.auto_awesome_rounded, size: 48, color: Theme.of(context).colorScheme.primary),
                    const SizedBox(height: AppSpacing.md),
                    Text('FluentX Pro feature', style: Theme.of(context).textTheme.headlineSmall, textAlign: TextAlign.center),
                    const SizedBox(height: AppSpacing.sm),
                    const Text('Upgrade to Monthly Pro or Annual Elite to unlock unlimited AI conversation practice.', textAlign: TextAlign.center),
                    const SizedBox(height: AppSpacing.lg),
                    FilledButton(
                      onPressed: () => context.push(RoutePaths.premium),
                      child: const Text('View Premium Plans'),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      );
    }

    final sessionState = ref.watch(aiPracticeSessionControllerProvider);

    if (_activeScenario != null && sessionState.summary != null) {
"""
replace_once(ai, old, new, 'AI Practice paid gating')

# Interview Coach: Annual Elite only.
interview = root / 'lib/features/interview_prep/presentation/screens/interview_prep_screen.dart'
ensure_import(
    interview,
    "import 'package:flutter_riverpod/flutter_riverpod.dart';\n",
    "import 'package:go_router/go_router.dart';\n",
    'Interview go_router import',
)
ensure_import(
    interview,
    "import '../../../../shared/widgets/widgets.dart';\n",
    "import '../../../../routes/route_paths.dart';\nimport '../../../premium/application/providers/membership_identity_provider.dart';\n",
    'Interview membership imports',
)
old = """  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('AI Interview Coach')),
"""
new = """  @override
  Widget build(BuildContext context) {
    final identityAsync = ref.watch(memberIdentityProvider);
    if (identityAsync.isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    final identity = identityAsync.valueOrNull;
    if (identity == null || identity.tier != FluentXMembershipTier.annual) {
      return Scaffold(
        appBar: AppBar(title: const Text('AI Interview Coach')),
        body: SafeArea(
          child: Center(
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.xl),
              child: AppCard(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.workspace_premium_rounded, size: 50, color: Color(0xFFD97706)),
                    const SizedBox(height: AppSpacing.md),
                    Text('FluentX Elite feature', style: Theme.of(context).textTheme.headlineSmall, textAlign: TextAlign.center),
                    const SizedBox(height: AppSpacing.sm),
                    Text(
                      identity?.tier == FluentXMembershipTier.monthly
                          ? 'Your Pro plan includes AI conversation practice. Upgrade to Annual Elite for advanced AI Interview Coach scoring and coaching.'
                          : 'Annual Elite unlocks advanced AI Interview Coach scoring, coaching tips and saved interview performance.',
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: AppSpacing.lg),
                    FilledButton(
                      onPressed: () => context.push(RoutePaths.premium),
                      child: const Text('Upgrade to Annual Elite'),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('AI Interview Coach')),
"""
replace_once(interview, old, new, 'Interview annual gating')

# Communication DNA advanced insights: Annual Elite only.
dna = root / 'lib/features/communication_dna/presentation/screens/communication_dna_screen.dart'
ensure_import(
    dna,
    "import 'package:flutter_riverpod/flutter_riverpod.dart';\n",
    "import 'package:go_router/go_router.dart';\n",
    'DNA go_router import',
)
ensure_import(
    dna,
    "import '../../../../shared/widgets/widgets.dart';\n",
    "import '../../../../routes/route_paths.dart';\nimport '../../../premium/application/providers/membership_identity_provider.dart';\n",
    'DNA membership imports',
)
old = """  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dnaAsync = ref.watch(communicationDnaProvider);

    return Scaffold(
"""
new = """  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final identityAsync = ref.watch(memberIdentityProvider);
    if (identityAsync.isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    final identity = identityAsync.valueOrNull;
    if (identity == null || identity.tier != FluentXMembershipTier.annual) {
      return Scaffold(
        appBar: AppBar(title: const Text('Communication DNA™')),
        body: SafeArea(
          child: Center(
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.xl),
              child: AppCard(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.insights_rounded, size: 50, color: Color(0xFFD97706)),
                    const SizedBox(height: AppSpacing.md),
                    Text('Advanced Elite insights', style: Theme.of(context).textTheme.headlineSmall, textAlign: TextAlign.center),
                    const SizedBox(height: AppSpacing.sm),
                    const Text('Annual Elite unlocks your full Communication DNA analysis, skill breakdown, strengths and focus-area insights.', textAlign: TextAlign.center),
                    const SizedBox(height: AppSpacing.lg),
                    FilledButton(
                      onPressed: () => context.push(RoutePaths.premium),
                      child: const Text('Unlock Annual Elite'),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      );
    }

    final dnaAsync = ref.watch(communicationDnaProvider);

    return Scaffold(
"""
replace_once(dna, old, new, 'Communication DNA annual gating')

print('FluentX subscription feature gating applied.')
