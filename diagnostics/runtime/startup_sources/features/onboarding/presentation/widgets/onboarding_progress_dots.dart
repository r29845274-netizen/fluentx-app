import 'package:flutter/material.dart';

import '../../../../core/constants/app_durations.dart';

class OnboardingProgressDots extends StatelessWidget {
  const OnboardingProgressDots({required this.count, required this.currentIndex, super.key});

  final int count;
  final int currentIndex;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(count, (index) {
        final isActive = index == currentIndex;
        return AnimatedContainer(
          duration: AppDurations.standard,
          margin: const EdgeInsets.symmetric(horizontal: 4),
          width: isActive ? 24 : 8,
          height: 8,
          decoration: BoxDecoration(
            color: isActive ? colorScheme.primary : colorScheme.outline,
            borderRadius: BorderRadius.circular(100),
          ),
        );
      }),
    );
  }
}
