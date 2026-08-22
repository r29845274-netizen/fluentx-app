from pathlib import Path
import shutil
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
repo_root = Path(__file__).resolve().parent.parent

# Ship the approved Maya portrait into the Flutter asset tree. pubspec already
# includes assets/images/ recursively through the directory declaration.
src_avatar = repo_root / 'scripts/assets/maya_tutor.jpg'
dst_avatar = root / 'assets/images/maya_tutor.jpg'
if not src_avatar.exists():
    raise SystemExit(f'Maya avatar asset not found: {src_avatar}')
dst_avatar.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(src_avatar, dst_avatar)
print(f'Maya avatar copied to {dst_avatar}')

screen = root / 'lib/features/ai_practice/presentation/screens/ai_practice_hub_screen.dart'
if not screen.exists():
    raise SystemExit(f'AI conversation screen not found: {screen}')

screen.write_text(r'''import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/app_radius.dart';
import '../../../../core/constants/app_spacing.dart';
import '../../../../core/error/failures.dart';
import '../../../../shared/widgets/widgets.dart';
import '../../../premium/application/providers/membership_identity_provider.dart';
import '../../application/providers/ai_practice_providers.dart';
import '../../domain/entities/practice_scenario.dart';
import '../widgets/chat_bubble.dart';
import '../widgets/practice_mic_button.dart';
import '../widgets/practice_summary_view.dart';

class AiPracticeHubScreen extends ConsumerStatefulWidget {
  const AiPracticeHubScreen({super.key});

  @override
  ConsumerState<AiPracticeHubScreen> createState() => _AiPracticeHubScreenState();
}

class _AiPracticeHubScreenState extends ConsumerState<AiPracticeHubScreen> {
  PracticeScenario? _activeScenario;
  final _scrollController = ScrollController();

  Future<void> _startScenario(PracticeScenario scenario) async {
    setState(() => _activeScenario = scenario);
    await ref.read(aiPracticeSessionControllerProvider.notifier).startSession(scenario.id);
  }

  void _exitToList() {
    ref.read(aiPracticeSessionControllerProvider.notifier).reset();
    setState(() => _activeScenario = null);
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  String _limitLabel(FluentXMembershipTier tier) => switch (tier) {
        FluentXMembershipTier.free => '1 hour/day',
        FluentXMembershipTier.monthly => '6 hours/day',
        FluentXMembershipTier.annual => '24 hours/day',
      };

  String _planLabel(FluentXMembershipTier tier) => switch (tier) {
        FluentXMembershipTier.free => 'Free',
        FluentXMembershipTier.monthly => 'Pro Monthly',
        FluentXMembershipTier.annual => 'Elite Annual',
      };

  @override
  Widget build(BuildContext context) {
    final identityAsync = ref.watch(memberIdentityProvider);
    final tier = identityAsync.valueOrNull?.tier ?? FluentXMembershipTier.free;
    final sessionState = ref.watch(aiPracticeSessionControllerProvider);

    if (_activeScenario != null && sessionState.summary != null) {
      return Scaffold(
        body: PracticeSummaryView(
          summary: sessionState.summary!,
          onDone: _exitToList,
        ),
      );
    }

    if (_activeScenario != null) {
      ref.listen(aiPracticeSessionControllerProvider, (previous, next) {
        if (next.messages.length != previous?.messages.length) _scrollToBottom();
      });

      return Scaffold(
        appBar: AppBar(
          leading: IconButton(
            tooltip: 'Close conversation',
            icon: const Icon(Icons.close),
            onPressed: _exitToList,
          ),
          titleSpacing: 0,
          title: Row(
            children: [
              const _MayaAvatar(size: 38),
              const SizedBox(width: AppSpacing.sm),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Maya', style: TextStyle(fontWeight: FontWeight.w800)),
                    Text(
                      _activeScenario!.title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.labelSmall?.copyWith(
                            color: Theme.of(context).colorScheme.onSurfaceVariant,
                          ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: sessionState.sessionId == null || sessionState.messages.isEmpty
                  ? null
                  : () => ref.read(aiPracticeSessionControllerProvider.notifier).endSession(),
              child: const Text('End'),
            ),
          ],
        ),
        body: SafeArea(
          top: false,
          child: Column(
            children: [
              Container(
                width: double.infinity,
                margin: const EdgeInsets.fromLTRB(
                  AppSpacing.base,
                  AppSpacing.sm,
                  AppSpacing.base,
                  0,
                ),
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.md,
                  vertical: AppSpacing.sm,
                ),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primaryContainer.withValues(alpha: .55),
                  borderRadius: AppRadius.mdAll,
                ),
                child: Row(
                  children: [
                    Icon(
                      Icons.record_voice_over_rounded,
                      size: 18,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                    const SizedBox(width: AppSpacing.sm),
                    Expanded(
                      child: Text(
                        'Speak naturally. Hindi/Hinglish is okay — Maya will explain it and help you retry in simple English.',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: sessionState.messages.isEmpty
                    ? _ConversationStarter(scenario: _activeScenario!)
                    : ListView.builder(
                        controller: _scrollController,
                        padding: const EdgeInsets.all(AppSpacing.base),
                        itemCount: sessionState.messages.length,
                        itemBuilder: (context, index) =>
                            ChatBubble(message: sessionState.messages[index]),
                      ),
              ),
              if (sessionState.error != null)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: AppSpacing.base),
                  child: Text(
                    sessionState.error!.uiMessage,
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Theme.of(context).colorScheme.error),
                  ),
                ),
              Padding(
                padding: const EdgeInsets.fromLTRB(
                  AppSpacing.base,
                  AppSpacing.sm,
                  AppSpacing.base,
                  AppSpacing.base,
                ),
                child: Column(
                  children: [
                    Text(
                      '${_planLabel(tier)} · AI Conversation ${_limitLabel(tier)} · resets daily',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.labelSmall?.copyWith(
                            color: Theme.of(context).colorScheme.onSurfaceVariant,
                          ),
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    sessionState.isSending
                        ? const LoadingWidget(message: 'Maya is thinking…')
                        : PracticeMicButton(
                            enabled: sessionState.sessionId != null,
                            onResult: (text) => ref
                                .read(aiPracticeSessionControllerProvider.notifier)
                                .sendUserMessage(text),
                          ),
                  ],
                ),
              ),
            ],
          ),
        ),
      );
    }

    final scenariosAsync = ref.watch(practiceScenariosProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('AI Conversation')),
      body: SafeArea(
        top: false,
        child: scenariosAsync.when(
          data: (scenarios) {
            if (scenarios.isEmpty) {
              return const EmptyStateWidget(title: 'No conversation topics available yet');
            }
            return RefreshIndicator(
              onRefresh: () async => ref.invalidate(practiceScenariosProvider),
              child: ListView(
                padding: const EdgeInsets.all(AppSpacing.base),
                children: [
                  _MayaHero(
                    tierLabel: _planLabel(tier),
                    limitLabel: _limitLabel(tier),
                  ),
                  const SizedBox(height: AppSpacing.lg),
                  Text(
                    'Choose a conversation',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Practice real situations with Maya. She adapts to your language and confidence level.',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                  ),
                  const SizedBox(height: AppSpacing.md),
                  ...scenarios.map(
                    (scenario) => Padding(
                      padding: const EdgeInsets.only(bottom: AppSpacing.md),
                      child: AppCard(
                        onTap: () => _startScenario(scenario),
                        child: Row(
                          children: [
                            Container(
                              width: 46,
                              height: 46,
                              decoration: BoxDecoration(
                                color: Theme.of(context).colorScheme.primary.withValues(alpha: .1),
                                borderRadius: AppRadius.mdAll,
                              ),
                              child: Icon(
                                Icons.forum_outlined,
                                color: Theme.of(context).colorScheme.primary,
                                size: 22,
                              ),
                            ),
                            const SizedBox(width: AppSpacing.md),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    scenario.title,
                                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                                          fontWeight: FontWeight.w700,
                                        ),
                                  ),
                                  const SizedBox(height: 3),
                                  Text(
                                    scenario.description,
                                    style: Theme.of(context).textTheme.bodySmall,
                                  ),
                                ],
                              ),
                            ),
                            Icon(
                              Icons.chevron_right,
                              color: Theme.of(context).colorScheme.onSurfaceVariant,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                ],
              ),
            );
          },
          loading: () => const LoadingWidget(message: 'Maya is getting ready…'),
          error: (_, __) => ErrorStateWidget(
            onRetry: () => ref.invalidate(practiceScenariosProvider),
          ),
        ),
      ),
    );
  }
}

class _MayaHero extends StatelessWidget {
  const _MayaHero({required this.tierLabel, required this.limitLabel});

  final String tierLabel;
  final String limitLabel;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [colors.primaryContainer, colors.secondaryContainer],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: AppRadius.lgAll,
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          const _MayaAvatar(size: 88),
          const SizedBox(width: AppSpacing.base),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Meet Maya',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900),
                ),
                const SizedBox(height: 3),
                Text(
                  'Your personal AI English tutor',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: AppSpacing.sm),
                Text(
                  'Talk in English, Hindi or Hinglish. Maya explains gently, corrects one useful mistake at a time, and keeps the conversation moving.',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                const SizedBox(height: AppSpacing.sm),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: colors.surface.withValues(alpha: .72),
                    borderRadius: AppRadius.fullAll,
                  ),
                  child: Text(
                    '$tierLabel · $limitLabel',
                    style: Theme.of(context).textTheme.labelMedium?.copyWith(fontWeight: FontWeight.w800),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ConversationStarter extends StatelessWidget {
  const _ConversationStarter({required this.scenario});

  final PracticeScenario scenario;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const _MayaAvatar(size: 104),
            const SizedBox(height: AppSpacing.base),
            Text(
              'Hi, I’m Maya 👋',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900),
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              'Let’s practice “${scenario.title}”. Tap the mic and say anything to begin. If English feels difficult, start in Hindi or Hinglish.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MayaAvatar extends StatelessWidget {
  const _MayaAvatar({required this.size});

  final double size;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      padding: const EdgeInsets.all(2),
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: Theme.of(context).colorScheme.surface,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: .12),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: ClipOval(
        child: Image.asset(
          'assets/images/maya_tutor.jpg',
          fit: BoxFit.cover,
          errorBuilder: (_, __, ___) => Container(
            color: Theme.of(context).colorScheme.primaryContainer,
            alignment: Alignment.center,
            child: Icon(
              Icons.support_agent_rounded,
              size: size * .46,
              color: Theme.of(context).colorScheme.primary,
            ),
          ),
        ),
      ),
    );
  }
}
''', encoding='utf-8')

print(f'Maya AI Conversation UI applied to {screen}')
print('Daily limits shown in app: Free 1h / Monthly 6h / Annual 24h.')
