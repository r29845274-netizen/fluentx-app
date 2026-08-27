from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')

home = root / 'lib/features/home/presentation/screens/home_screen.dart'
goal = root / 'lib/features/home/presentation/widgets/daily_goal_card.dart'
stat = root / 'lib/features/home/presentation/widgets/stat_chip.dart'
for p in (home, goal, stat):
    if not p.exists():
        raise SystemExit(f'Missing Home UI source: {p}')

home.write_text(r'''import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../routes/route_paths.dart';
import '../../../../shared/widgets/widgets.dart';
import '../../application/providers/home_providers.dart';
import '../../domain/entities/home_summary.dart';
import '../widgets/continue_learning_card.dart';
import '../widgets/daily_goal_card.dart';
import '../widgets/quick_action_grid.dart';
import '../widgets/stat_chip.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final homeSummaryAsync = ref.watch(homeSummaryProvider);
    return Scaffold(
      body: SafeArea(
        child: homeSummaryAsync.when(
          data: (summary) => _HomeContent(summary: summary),
          loading: () => const _HomeLoadingSkeleton(),
          error: (_, __) => ErrorStateWidget(
            message: "We couldn't load your dashboard right now.",
            onRetry: () => ref.invalidate(homeSummaryProvider),
          ),
        ),
      ),
    );
  }
}

class _HomeContent extends ConsumerWidget {
  const _HomeContent({required this.summary});
  final HomeSummary summary;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final textTheme = theme.textTheme;
    final colors = theme.colorScheme;
    final challengeDone = summary.streakDays.clamp(0, 5);

    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(homeSummaryProvider),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 28),
        children: [
          Row(children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                gradient: LinearGradient(colors: [colors.primary, colors.tertiary]),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(Icons.auto_awesome_rounded, color: colors.onPrimary, size: 18),
            ),
            const SizedBox(width: 9),
            Text(
              'Fluent X',
              style: textTheme.titleMedium?.copyWith(
                color: colors.primary,
                fontWeight: FontWeight.w900,
                letterSpacing: .2,
              ),
            ),
            const Spacer(),
            Stack(children: [
              IconButton(
                tooltip: 'Notification settings',
                onPressed: () => context.push(RoutePaths.settings),
                icon: Icon(Icons.notifications_none_rounded, color: colors.onSurface),
              ),
              Positioned(
                right: 10,
                top: 9,
                child: Container(
                  width: 7,
                  height: 7,
                  decoration: BoxDecoration(color: colors.primary, shape: BoxShape.circle),
                ),
              ),
            ]),
          ]),
          const SizedBox(height: 12),
          Text(
            'Hi, ${summary.greetingName} 👋',
            style: textTheme.headlineLarge?.copyWith(fontWeight: FontWeight.w900, letterSpacing: -.7),
          ),
          const SizedBox(height: 4),
          Text(
            'Small steps every day build real fluency.',
            style: textTheme.bodyLarge?.copyWith(color: colors.onSurfaceVariant, height: 1.3),
          ),
          const SizedBox(height: 22),
          DailyGoalCard(
            targetMinutes: summary.dailyGoalTargetMinutes,
            progressMinutes: summary.dailyGoalProgressMinutes,
            progress: summary.dailyGoalProgress,
          ),
          const SizedBox(height: 12),
          Row(children: [
            StatChip(
              icon: Icons.local_fire_department_rounded,
              iconColor: const Color(0xFFFF641E),
              value: '${summary.streakDays}',
              label: 'Day Streak',
            ),
            const SizedBox(width: 12),
            StatChip(
              icon: Icons.emoji_events_rounded,
              iconColor: const Color(0xFFFFB21A),
              value: '${summary.xpEarned}',
              label: 'XP Earned',
            ),
          ]),
          const SizedBox(height: 24),
          _SectionHeader(
            title: 'Quick Actions',
            action: 'View all',
            onTap: () => context.push(RoutePaths.learn),
          ),
          const SizedBox(height: 10),
          const QuickActionGrid(),
          const SizedBox(height: 24),
          _SectionHeader(title: 'Continue Learning'),
          const SizedBox(height: 10),
          if (summary.continueLearning != null)
            ContinueLearningCard(
              item: summary.continueLearning!,
              onTap: () => context.push(RoutePaths.learn),
            )
          else
            _StarterLearningCard(onTap: () => context.push(RoutePaths.learn)),
          const SizedBox(height: 24),
          _SectionHeader(
            title: 'Recommended for You',
            action: 'View all',
            onTap: () => context.push(RoutePaths.learn),
          ),
          const SizedBox(height: 10),
          Row(children: [
            Expanded(
              child: _RecommendationCard(
                icon: Icons.forum_rounded,
                title: 'Maya Conversation',
                subtitle: 'Real-life dialogues with AI',
                tag: 'Speaking',
                onTap: () => context.push(RoutePaths.learn),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _RecommendationCard(
                icon: Icons.graphic_eq_rounded,
                title: 'Pronunciation Practice',
                subtitle: 'Speak clearly and confidently',
                tag: 'All Levels',
                onTap: () => context.push(RoutePaths.learn),
              ),
            ),
          ]),
          const SizedBox(height: 24),
          _SectionHeader(title: "This Week's Challenge", action: challengeDone >= 5 ? 'Completed' : 'Keep going'),
          const SizedBox(height: 10),
          _WeeklyChallengeCard(done: challengeDone, onTap: () => context.push(RoutePaths.learn)),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title, this.action, this.onTap});
  final String title;
  final String? action;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Row(children: [
      Expanded(
        child: Text(
          title,
          style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900, letterSpacing: -.3),
        ),
      ),
      if (action != null)
        TextButton(
          onPressed: onTap,
          style: TextButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2)),
          child: Text(action!, style: TextStyle(color: colors.primary, fontWeight: FontWeight.w700)),
        ),
    ]);
  }
}

class _StarterLearningCard extends StatelessWidget {
  const _StarterLearningCard({required this.onTap});
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Material(
      color: colors.surfaceContainer,
      borderRadius: BorderRadius.circular(20),
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: colors.outlineVariant.withValues(alpha: .75)),
          ),
          child: Row(children: [
            Container(
              width: 78,
              height: 78,
              decoration: BoxDecoration(
                gradient: LinearGradient(colors: [colors.primaryContainer, colors.secondaryContainer]),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(Icons.headphones_rounded, color: colors.primary, size: 38),
            ),
            const SizedBox(width: 14),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('NEXT LESSON', style: TextStyle(color: colors.primary, fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: .8)),
              const SizedBox(height: 4),
              Text('Start your learning path', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
              const SizedBox(height: 4),
              Text('Personalized English practice', style: Theme.of(context).textTheme.bodySmall?.copyWith(color: colors.onSurfaceVariant)),
            ])),
            FilledButton.tonal(onPressed: onTap, child: const Text('Start')),
          ]),
        ),
      ),
    );
  }
}

class _RecommendationCard extends StatelessWidget {
  const _RecommendationCard({required this.icon, required this.title, required this.subtitle, required this.tag, required this.onTap});
  final IconData icon;
  final String title;
  final String subtitle;
  final String tag;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Material(
      color: colors.surfaceContainer,
      borderRadius: BorderRadius.circular(20),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(20),
        child: Container(
          constraints: const BoxConstraints(minHeight: 176),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: colors.outlineVariant.withValues(alpha: .7)),
          ),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                gradient: LinearGradient(colors: [colors.primary, colors.tertiary]),
                borderRadius: BorderRadius.circular(15),
              ),
              child: Icon(icon, color: colors.onPrimary, size: 25),
            ),
            const SizedBox(height: 12),
            Text(title, maxLines: 2, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 4),
            Text(subtitle, maxLines: 2, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: colors.onSurfaceVariant, height: 1.3)),
            const Spacer(),
            Container(
              margin: const EdgeInsets.only(top: 10),
              padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
              decoration: BoxDecoration(color: colors.primaryContainer, borderRadius: BorderRadius.circular(99)),
              child: Text(tag, style: TextStyle(color: colors.onPrimaryContainer, fontSize: 11, fontWeight: FontWeight.w800)),
            ),
          ]),
        ),
      ),
    );
  }
}

class _WeeklyChallengeCard extends StatelessWidget {
  const _WeeklyChallengeCard({required this.done, required this.onTap});
  final int done;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Material(
      color: colors.surfaceContainer,
      borderRadius: BorderRadius.circular(22),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(22),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(22),
            border: Border.all(color: colors.primary.withValues(alpha: .32)),
          ),
          child: Row(children: [
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                color: colors.primaryContainer,
                shape: BoxShape.circle,
                border: Border.all(color: colors.primary.withValues(alpha: .4), width: 2),
              ),
              child: Icon(Icons.workspace_premium_rounded, color: colors.primary, size: 32),
            ),
            const SizedBox(width: 14),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Consistency Champion', style: Theme.of(context).textTheme.titleMedium?.copyWith(color: colors.primary, fontWeight: FontWeight.w900)),
              const SizedBox(height: 3),
              Text('Complete 5 learning sessions this week', style: Theme.of(context).textTheme.bodySmall?.copyWith(color: colors.onSurfaceVariant)),
              const SizedBox(height: 12),
              Row(children: [
                for (var i = 0; i < 5; i++) ...[
                  Icon(i < done ? Icons.check_circle_rounded : Icons.circle_outlined, color: i < done ? colors.primary : colors.outline, size: 20),
                  if (i != 4) const SizedBox(width: 6),
                ],
                const Spacer(),
                Text('$done / 5', style: const TextStyle(fontWeight: FontWeight.w900)),
              ]),
            ])),
            const SizedBox(width: 6),
            Icon(Icons.chevron_right_rounded, color: colors.onSurfaceVariant),
          ]),
        ),
      ),
    );
  }
}

class _HomeLoadingSkeleton extends StatelessWidget {
  const _HomeLoadingSkeleton();

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(AppSpacing.base),
      children: const [
        LoadingCardSkeleton(lines: 2),
        SizedBox(height: AppSpacing.md),
        LoadingCardSkeleton(lines: 3),
        SizedBox(height: AppSpacing.md),
        LoadingCardSkeleton(lines: 2),
        SizedBox(height: AppSpacing.xl),
        LoadingCardSkeleton(lines: 4),
      ],
    );
  }
}
''')

goal.write_text(r'''import 'package:flutter/material.dart';

class DailyGoalCard extends StatelessWidget {
  const DailyGoalCard({
    required this.targetMinutes,
    required this.progressMinutes,
    required this.progress,
    super.key,
  });

  final int targetMinutes;
  final int progressMinutes;
  final double progress;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final textTheme = Theme.of(context).textTheme;
    final safeProgress = progress.clamp(0.0, 1.0).toDouble();
    final percent = (safeProgress * 100).round();

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            colors.primaryContainer.withValues(alpha: .68),
            colors.surfaceContainerHighest,
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: colors.primary.withValues(alpha: .32)),
        boxShadow: [
          BoxShadow(
            color: colors.primary.withValues(alpha: .08),
            blurRadius: 22,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Row(children: [
        Container(
          width: 62,
          height: 62,
          decoration: BoxDecoration(
            color: colors.primary.withValues(alpha: .14),
            shape: BoxShape.circle,
            border: Border.all(color: colors.primary.withValues(alpha: .25)),
          ),
          child: Icon(Icons.gps_fixed_rounded, color: colors.primary, size: 31),
        ),
        const SizedBox(width: 16),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('DAILY GOAL', style: textTheme.labelMedium?.copyWith(color: colors.primary, fontWeight: FontWeight.w900, letterSpacing: .8)),
          const SizedBox(height: 3),
          Text('Speak for $targetMinutes minutes', style: textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
          const SizedBox(height: 12),
          ClipRRect(
            borderRadius: BorderRadius.circular(99),
            child: LinearProgressIndicator(
              value: safeProgress,
              minHeight: 9,
              backgroundColor: colors.outlineVariant.withValues(alpha: .55),
            ),
          ),
          const SizedBox(height: 6),
          Text('$progressMinutes of $targetMinutes min today', style: textTheme.bodySmall?.copyWith(color: colors.onSurfaceVariant)),
        ])),
        const SizedBox(width: 14),
        SizedBox(
          width: 62,
          height: 62,
          child: Stack(alignment: Alignment.center, children: [
            CircularProgressIndicator(
              value: safeProgress,
              strokeWidth: 6,
              backgroundColor: colors.outlineVariant.withValues(alpha: .6),
            ),
            Text('$percent%', style: textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
          ]),
        ),
      ]),
    );
  }
}
''')

stat.write_text(r'''import 'package:flutter/material.dart';

class StatChip extends StatelessWidget {
  const StatChip({
    required this.icon,
    required this.iconColor,
    required this.value,
    required this.label,
    super.key,
  });

  final IconData icon;
  final Color iconColor;
  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final textTheme = Theme.of(context).textTheme;
    final helper = label == 'Day Streak' ? 'Keep it going!' : 'Learn. Practice. Grow.';

    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(15),
        decoration: BoxDecoration(
          color: colors.surfaceContainer,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: colors.outlineVariant.withValues(alpha: .72)),
        ),
        child: Row(children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(color: iconColor.withValues(alpha: .12), borderRadius: BorderRadius.circular(14)),
            child: Icon(icon, color: iconColor, size: 25),
          ),
          const SizedBox(width: 11),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(value, style: textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
            Text(label, style: textTheme.bodySmall?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 2),
            Text(helper, maxLines: 1, overflow: TextOverflow.ellipsis, style: textTheme.labelSmall?.copyWith(color: colors.onSurfaceVariant)),
          ])),
        ]),
      ),
    );
  }
}
''')

print('Applied premium Home UI: learning-first layout, recommendations, challenge, improved goal and stats.')
