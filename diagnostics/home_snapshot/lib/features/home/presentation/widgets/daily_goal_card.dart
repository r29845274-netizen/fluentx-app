import 'package:flutter/material.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../shared/widgets/widgets.dart';

/// "Daily Goal" card on Home — shows the day's speaking-practice
/// target and how much of it is done, as a linear progress bar.
class DailyGoalCard extends StatelessWidget {
  const DailyGoalCard({
    required this.targetMinutes,
    required this.progressMinutes,
    required this.progress,
    super.key,
  });

  final int targetMinutes;
  final int progressMinutes;

  /// 0.0–1.0
  final double progress;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final textTheme = Theme.of(context).textTheme;

    return AppCard(
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: colorScheme.primary.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Icon(Icons.gps_fixed, color: colorScheme.primary, size: 22),
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Daily Goal', style: textTheme.bodySmall),
                const SizedBox(height: 2),
                Text(
                  'Speak for $targetMinutes minutes',
                  style: textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: AppSpacing.sm),
                ClipRRect(
                  borderRadius: BorderRadius.circular(100),
                  child: LinearProgressIndicator(
                    value: progress,
                    minHeight: 6,
                    backgroundColor: colorScheme.outline,
                    valueColor: AlwaysStoppedAnimation<Color>(colorScheme.primary),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '$progressMinutes of $targetMinutes min today',
                  style: textTheme.labelSmall,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
