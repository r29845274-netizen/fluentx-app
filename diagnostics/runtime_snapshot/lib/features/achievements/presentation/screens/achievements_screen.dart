import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/router/onboarding_status_provider.dart';
import '../../../../routes/route_paths.dart';
import '../../../../shared/widgets/widgets.dart';
import '../../application/providers/achievements_providers.dart';
import '../../domain/entities/achievement_stats.dart';
import '../widgets/achievement_badge.dart';

class AchievementsScreen extends ConsumerWidget {
  const AchievementsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final statsAsync = ref.watch(achievementStatsProvider);
    final onboardingComplete = ref.watch(onboardingCompleteProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Achievements')),
      body: SafeArea(
        top: false,
        child: statsAsync.when(
          data: (stats) => _AchievementsGrid(
            stats: stats,
            firstStepsUnlocked: onboardingComplete,
          ),
          loading: () => const LoadingWidget(),
          error: (_, __) => ErrorStateWidget(
            onRetry: () => ref.invalidate(achievementStatsProvider),
          ),
        ),
      ),
    );
  }
}

class _AchievementsGrid extends StatelessWidget {
  const _AchievementsGrid({required this.stats, required this.firstStepsUnlocked});

  final AchievementStats stats;
  final bool firstStepsUnlocked;

  @override
  Widget build(BuildContext context) {
    final badges = [
      (
        title: 'First Steps',
        subtitle: 'Complete onboarding',
        icon: Icons.directions_walk,
        gradient: const [Color(0xFF2563EB), Color(0xFF60A5FA)],
        unlocked: firstStepsUnlocked,
      ),
      (
        title: '7 Day Streak',
        subtitle: 'Keep it up!',
        icon: Icons.local_fire_department_outlined,
        gradient: const [Color(0xFFEA580C), Color(0xFFFB923C)],
        unlocked: stats.streakDays >= 7,
      ),
      (
        title: '30 Day Streak',
        subtitle: 'Amazing!',
        icon: Icons.emoji_events_outlined,
        gradient: const [Color(0xFF16A34A), Color(0xFF4ADE80)],
        unlocked: stats.streakDays >= 30,
      ),
      (
        title: 'AI Conversation',
        subtitle: 'Complete 10 chats',
        icon: Icons.chat_bubble_outline,
        gradient: const [Color(0xFF9333EA), Color(0xFFC084FC)],
        unlocked: stats.aiSessionCount >= 10,
      ),
      (
        title: '1000 Minutes',
        subtitle: 'Practice time',
        icon: Icons.schedule,
        gradient: const [Color(0xFFD97706), Color(0xFFFBBF24)],
        unlocked: stats.totalPracticeMinutes >= 1000,
      ),
      (
        title: 'Vocabulary Hero',
        subtitle: 'Learn 500 words',
        icon: Icons.star_border,
        gradient: const [Color(0xFF0891B2), Color(0xFF67E8F9)],
        unlocked: stats.vocabularyMasteredCount >= 500,
      ),
    ];

    final unlockedCount = badges.where((b) => b.unlocked).length;

    return ListView(
      padding: const EdgeInsets.all(AppSpacing.base),
      children: [
        AppCard(
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.workspace_premium_outlined, color: Theme.of(context).colorScheme.primary),
              const SizedBox(width: AppSpacing.sm),
              Text(
                '$unlockedCount of ${badges.length} unlocked',
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
              ),
            ],
          ),
        ),
        FilledButton.icon(
          onPressed: () => context.push('${RoutePaths.shareProgress}?mode=achievement'),
          icon: const Icon(Icons.ios_share_rounded),
          label: const Text('Share Achievement'),
        ),
        const SizedBox(height: AppSpacing.lg),
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: badges.length,
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 3,
            mainAxisSpacing: AppSpacing.lg,
            crossAxisSpacing: AppSpacing.sm,
            childAspectRatio: 0.8,
          ),
          itemBuilder: (context, index) {
            final badge = badges[index];
            return AchievementBadge(
              title: badge.title,
              subtitle: badge.subtitle,
              icon: badge.icon,
              gradient: badge.gradient,
              isUnlocked: badge.unlocked,
            );
          },
        ),
      ],
    );
  }
}
