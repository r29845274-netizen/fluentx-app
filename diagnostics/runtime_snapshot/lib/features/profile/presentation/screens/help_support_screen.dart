import 'package:flutter/material.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../shared/widgets/widgets.dart';

class HelpSupportScreen extends StatelessWidget {
  const HelpSupportScreen({super.key});

  static const _faqs = [
    ('How is my Communication DNA™ calculated?', 'Your practice activity is combined into Fluency, Vocabulary, Grammar, Pronunciation and Confidence scores.'),
    ('Why is my daily goal not updating?', 'Pull to refresh Home after saving a new goal. Make sure you are signed in and online.'),
    ('How do AI Practice sessions work?', 'Choose a scenario, speak or type your response, review inline corrections, then end the session for a summary.'),
    ('How do achievements unlock?', 'Badges unlock automatically when your streak, practice time, AI sessions or vocabulary milestones reach the required level.'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Help & Support')),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.base),
        children: [
          AppCard(
            child: Row(
              children: [
                Icon(Icons.support_agent, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: AppSpacing.md),
                const Expanded(child: Text('Find quick answers for the most common Fluent X questions.')),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.lg),
          Text('Frequently Asked Questions', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: AppSpacing.sm),
          for (final faq in _faqs)
            Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.sm),
              child: AppCard(
                child: ExpansionTile(
                  tilePadding: EdgeInsets.zero,
                  childrenPadding: const EdgeInsets.only(top: AppSpacing.sm),
                  title: Text(faq.$1),
                  children: [Align(alignment: Alignment.centerLeft, child: Text(faq.$2))],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
