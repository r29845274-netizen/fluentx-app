import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../routes/route_paths.dart';
import '../../../../shared/widgets/widgets.dart';
import '../../../communication_dna/application/providers/communication_dna_providers.dart';

class ProgressScreen extends ConsumerWidget {
  const ProgressScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dnaAsync = ref.watch(communicationDnaProvider);
    final colorScheme = Theme.of(context).colorScheme;
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(title: const Text('Progress')),
      body: SafeArea(
        top: false,
        child: ListView(
          padding: const EdgeInsets.all(AppSpacing.base),
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: colorScheme.primaryContainer.withValues(alpha: .48),
                borderRadius: BorderRadius.circular(18),
              ),
              child: Row(children: [
                const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('Share your progress', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 17)),
                  SizedBox(height: 3),
                  Text('Create a clean Fluent X progress card for WhatsApp or social media.'),
                ])),
                FilledButton.tonalIcon(
                  onPressed: () => context.push('${RoutePaths.shareProgress}?mode=progress'),
                  icon: const Icon(Icons.ios_share_rounded),
                  label: const Text('Share'),
                ),
              ]),
            ),
            const SizedBox(height: AppSpacing.xl),
            Text('Communication DNA™', style: textTheme.headlineSmall),
            const SizedBox(height: AppSpacing.sm),
            dnaAsync.when(
              data: (dna) => AppCard(
                onTap: () => context.push(RoutePaths.communicationDna),
                child: Column(
                  children: [
                    Row(
                      children: [
                        SizedBox(
                          width: 72,
                          height: 72,
                          child: Stack(
                            alignment: Alignment.center,
                            children: [
                              CircularProgressIndicator(
                                value: dna.overallScore / 100,
                                strokeWidth: 7,
                                backgroundColor: colorScheme.outline,
                                valueColor: AlwaysStoppedAnimation<Color>(colorScheme.primary),
                              ),
                              Text('${dna.overallScore}%', style: textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w700)),
                            ],
                          ),
                        ),
                        const SizedBox(width: AppSpacing.md),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(dna.levelLabel, style: textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w600)),
                              const SizedBox(height: 2),
                              Text('Strong in ${dna.strengths.join(' & ')}', style: textTheme.bodySmall),
                            ],
                          ),
                        ),
                        Icon(Icons.chevron_right, color: colorScheme.onSurfaceVariant),
                      ],
                    ),
                    const SizedBox(height: AppSpacing.lg),
                    for (final entry in dna.componentsByLabel.entries) ...[
                      _SkillBar(label: entry.key, value: entry.value),
                      if (entry.key != dna.componentsByLabel.keys.last)
                        const SizedBox(height: AppSpacing.sm),
                    ],
                  ],
                ),
              ),
              loading: () => const LoadingCardSkeleton(lines: 5),
              error: (_, __) => AppCard(
                child: Column(
                  children: [
                    Icon(Icons.insights_outlined, size: 42, color: colorScheme.primary),
                    const SizedBox(height: AppSpacing.sm),
                    Text('Your Communication DNA is building', style: textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
                    const SizedBox(height: AppSpacing.xs),
                    const Text('Complete speaking, grammar and writing practice to generate your skill profile.', textAlign: TextAlign.center),
                    const SizedBox(height: AppSpacing.md),
                    OutlinedButton.icon(
                      onPressed: () => ref.invalidate(communicationDnaProvider),
                      icon: const Icon(Icons.refresh_rounded),
                      label: const Text('Refresh'),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.xl),
            Text('Achievements', style: textTheme.headlineSmall),
            const SizedBox(height: AppSpacing.sm),
            AppCard(
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
            const SizedBox(height: AppSpacing.xl),
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
          ],
        ),
      ),
    );
  }
}

class _SkillBar extends StatelessWidget {
  const _SkillBar({required this.label, required this.value});

  final String label;
  final int value;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        SizedBox(width: 96, child: Text(label, style: Theme.of(context).textTheme.bodySmall)),
        Expanded(
          child: ClipRRect(
            borderRadius: BorderRadius.circular(100),
            child: LinearProgressIndicator(value: value / 100, minHeight: 7),
          ),
        ),
        const SizedBox(width: AppSpacing.sm),
        SizedBox(width: 34, child: Text('$value%', textAlign: TextAlign.right, style: Theme.of(context).textTheme.bodySmall)),
      ],
    );
  }
}
