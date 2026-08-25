import 'package:flutter/material.dart';

import '../../../../core/constants/app_radius.dart';
import '../../../../core/constants/app_spacing.dart';
import '../../domain/entities/onboarding_goal.dart';

class GoalOptionCard extends StatelessWidget {
  const GoalOptionCard({
    required this.goal,
    required this.isSelected,
    required this.onTap,
    super.key,
  });

  final OnboardingGoal goal;
  final bool isSelected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return InkWell(
      onTap: onTap,
      borderRadius: AppRadius.lgAll,
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.base),
        decoration: BoxDecoration(
          borderRadius: AppRadius.lgAll,
          border: Border.all(
            color: isSelected ? colorScheme.primary : colorScheme.outline,
            width: isSelected ? 2 : 1,
          ),
          color: isSelected ? colorScheme.primary.withValues(alpha: 0.06) : colorScheme.surface,
        ),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: colorScheme.primary.withValues(alpha: 0.1),
                borderRadius: AppRadius.mdAll,
              ),
              child: Icon(goal.icon, color: colorScheme.primary, size: 22),
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    goal.label,
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                  ),
                  const SizedBox(height: 2),
                  Text(goal.description, style: Theme.of(context).textTheme.bodySmall),
                ],
              ),
            ),
            if (isSelected)
              Icon(Icons.check_circle, color: colorScheme.primary, size: 22),
          ],
        ),
      ),
    );
  }
}
