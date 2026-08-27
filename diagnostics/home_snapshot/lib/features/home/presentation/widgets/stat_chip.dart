import 'package:flutter/material.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../shared/widgets/widgets.dart';

/// Compact stat display used for "Day Streak" and "XP Earned" on Home.
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
    final textTheme = Theme.of(context).textTheme;

    return Expanded(
      child: AppCard(
        child: Row(
          children: [
            Icon(icon, color: iconColor, size: 22),
            const SizedBox(width: AppSpacing.sm),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(value, style: textTheme.headlineSmall),
                Text(label, style: textTheme.labelSmall),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
