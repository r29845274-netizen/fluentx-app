import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_radius.dart';
import '../../../../core/constants/app_spacing.dart';
import '../../../../shared/widgets/widgets.dart';
import '../../../../routes/route_paths.dart';
import '../../../premium/application/providers/membership_identity_provider.dart';
import '../../application/providers/communication_dna_providers.dart';
import '../../domain/entities/communication_dna.dart';

class CommunicationDnaScreen extends ConsumerWidget {
  const CommunicationDnaScreen({super.key});

  @override
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
      appBar: AppBar(title: const Text('Communication DNA™')),
      body: SafeArea(
        top: false,
        child: dnaAsync.when(
          data: (dna) => _DnaContent(dna: dna),
          loading: () => const LoadingWidget(),
          error: (_, __) => ErrorStateWidget(
            onRetry: () => ref.invalidate(communicationDnaProvider),
          ),
        ),
      ),
    );
  }
}

class _DnaContent extends StatelessWidget {
  const _DnaContent({required this.dna});

  final CommunicationDna dna;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final textTheme = Theme.of(context).textTheme;

    return ListView(
      padding: const EdgeInsets.all(AppSpacing.base),
      children: [
        Center(
          child: Column(
            children: [
              Text('Overall Score', style: textTheme.bodyMedium),
              const SizedBox(height: AppSpacing.xs),
              Text(
                '${dna.overallScore}%',
                style: textTheme.displayLarge?.copyWith(fontSize: 48, color: colorScheme.primary),
              ),
              Container(
                margin: const EdgeInsets.only(top: 4),
                padding: const EdgeInsets.symmetric(horizontal: AppSpacing.sm, vertical: 2),
                decoration: BoxDecoration(
                  color: colorScheme.primary.withValues(alpha: 0.1),
                  borderRadius: AppRadius.fullAll,
                ),
                child: Text(
                  dna.levelLabel,
                  style: textTheme.labelSmall?.copyWith(
                    color: colorScheme.primary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.lg),
        Center(
          child: CommunicationDnaRadarChart(values: dna.componentsByLabel),
        ),
        const SizedBox(height: AppSpacing.lg),
        AppCard(
          child: Column(
            children: [
              for (final entry in dna.componentsByLabel.entries) ...[
                _ScoreRow(label: entry.key, value: entry.value),
                if (entry.key != dna.componentsByLabel.entries.last.key)
                  const SizedBox(height: AppSpacing.sm),
              ],
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.base),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.trending_up, size: 18, color: const Color(0xFF16A34A)),
                  const SizedBox(width: AppSpacing.xs),
                  Text(
                    'Strength: ${dna.strengths.join(', ')}',
                    style: textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.sm),
              Row(
                children: [
                  Icon(Icons.flag_outlined, size: 18, color: const Color(0xFFD97706)),
                  const SizedBox(width: AppSpacing.xs),
                  Expanded(
                    child: Text(
                      'Focus on: ${dna.focusAreas.join(', ')}',
                      style: textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.xl),
      ],
    );
  }
}

class _ScoreRow extends StatelessWidget {
  const _ScoreRow({required this.label, required this.value});

  final String label;
  final int value;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Row(
      children: [
        SizedBox(
          width: 100,
          child: Text(label, style: Theme.of(context).textTheme.bodyMedium),
        ),
        Expanded(
          child: ClipRRect(
            borderRadius: BorderRadius.circular(100),
            child: LinearProgressIndicator(
              value: value / 100,
              minHeight: 8,
              backgroundColor: colorScheme.outline,
              valueColor: AlwaysStoppedAnimation<Color>(colorScheme.primary),
            ),
          ),
        ),
        const SizedBox(width: AppSpacing.sm),
        SizedBox(
          width: 36,
          child: Text(
            '$value%',
            textAlign: TextAlign.end,
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ),
      ],
    );
  }
}
