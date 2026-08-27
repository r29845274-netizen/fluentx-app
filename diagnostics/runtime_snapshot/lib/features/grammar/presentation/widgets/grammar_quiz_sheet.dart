import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/app_radius.dart';
import '../../../../core/constants/app_spacing.dart';
import '../../../../shared/widgets/widgets.dart';
import '../../../authentication/application/providers/auth_providers.dart';
import '../../application/providers/grammar_providers.dart';
import '../../domain/entities/grammar_lesson.dart';

/// Quiz flow for one lesson, shown inside an [AppBottomSheet]. Tracks
/// score locally (this is a single short session, not something that
/// needs to survive navigation) and records a mistake via
/// [recordGrammarMistakeUseCaseProvider] for every wrong answer.
class GrammarQuizSheet extends ConsumerStatefulWidget {
  const GrammarQuizSheet({required this.lesson, super.key});

  final GrammarLesson lesson;

  @override
  ConsumerState<GrammarQuizSheet> createState() => _GrammarQuizSheetState();
}

class _GrammarQuizSheetState extends ConsumerState<GrammarQuizSheet> {
  int _currentIndex = 0;
  int? _selectedOption;
  int _correctCount = 0;

  List<GrammarQuestion> _fallbackQuestions(GrammarLesson lesson) {
    final data = switch (lesson.title) {
      'Clear Pronoun Reference' => const [
          ('Which sentence has the clearest pronoun reference?', ['When Maya spoke to Riya, she smiled.', 'Riya smiled after Maya spoke to her.', 'She spoke to her and smiled.', 'When she arrived, she called her.'], 1),
          ('Choose the clearest sentence.', ['Aman told Raj that he was late.', 'Aman told Raj, “You are late.”', 'He told him he was late.', 'When he met him, he apologized.'], 1),
        ],
      'Each, Every, All, and Both' => const [
          ('___ student must bring an ID card.', ['All', 'Every', 'Both', 'Many'], 1),
          ('___ of the two answers are correct.', ['Each', 'Every', 'Both', 'All of'], 2),
        ],
      'Who, Whom, and Whose' => const [
          ('___ laptop is on the desk?', ['Who', 'Whom', 'Whose', 'Which person'], 2),
          ('To ___ did you send the email?', ['who', 'whom', 'whose', 'who’s'], 1),
        ],
      'Fewer and Less' => const [
          ('We had ___ meetings this week.', ['less', 'fewer', 'little', 'least'], 1),
          ('There is ___ traffic today.', ['fewer', 'few', 'less', 'many'], 2),
        ],
      'Say, Tell, Speak, and Talk' => const [
          ('Please ___ me the truth.', ['say', 'tell', 'speak', 'talk'], 1),
          ('Can I ___ to the manager?', ['say', 'tell', 'speak', 'told'], 2),
        ],
      'Make, Do, Take, and Have Collocations' => const [
          ('We need to ___ a decision today.', ['do', 'make', 'take', 'have'], 1),
          ('Please ___ notes during the meeting.', ['make', 'do', 'take', 'have'], 2),
        ],
      'Used To, Be Used To, Get Used To' => const [
          ('I ___ wake up early when I was in school.', ['am used to', 'used to', 'get used to', 'using to'], 1),
          ('She is ___ working from home now.', ['used to', 'use to', 'get use to', 'used for'], 0),
        ],
      _ => const <(String, List<String>, int)>[],
    };
    return List<GrammarQuestion>.generate(data.length, (index) {
      final row = data[index];
      return GrammarQuestion(
        id: 'local-${lesson.id}-$index',
        lessonId: lesson.id,
        questionText: row.$1,
        options: row.$2,
        correctIndex: row.$3,
      );
    });
  }

  Future<void> _selectOption(int index, GrammarQuestion question) async {
    if (_selectedOption != null) return;
    setState(() => _selectedOption = index);

    if (index == question.correctIndex) {
      _correctCount++;
    } else {
      final userId = ref.read(authStateChangesProvider).value?.id;
      if (userId != null) {
        await ref
            .read(recordGrammarMistakeUseCaseProvider)
            .call(userId: userId, category: widget.lesson.category);
      }
    }
  }

  void _next(int totalQuestions) {
    if (_currentIndex + 1 >= totalQuestions) {
      setState(() => _currentIndex = totalQuestions); // signals "complete"
    } else {
      setState(() {
        _currentIndex++;
        _selectedOption = null;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final questionsAsync = ref.watch(grammarQuestionsProvider(widget.lesson.id));

    return questionsAsync.when(
      data: (questions) {
        final effectiveQuestions = questions.isEmpty
            ? _fallbackQuestions(widget.lesson)
            : questions;
        if (effectiveQuestions.isEmpty) {
          return EmptyStateWidget(
            title: 'Practice is being prepared',
            message: 'This lesson explanation is available now. Pull to refresh or try the quiz again shortly.',
          );
        }
        if (_currentIndex >= effectiveQuestions.length) {
          return _QuizResult(correctCount: _correctCount, total: effectiveQuestions.length);
        }

        final question = effectiveQuestions[_currentIndex];
        final colorScheme = Theme.of(context).colorScheme;

        return Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Question ${_currentIndex + 1} of ${effectiveQuestions.length}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(question.questionText, style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: AppSpacing.base),
            for (var i = 0; i < question.options.length; i++) ...[
              _OptionTile(
                label: question.options[i],
                state: _selectedOption == null
                    ? _OptionState.neutral
                    : i == question.correctIndex
                        ? _OptionState.correct
                        : i == _selectedOption
                            ? _OptionState.incorrect
                            : _OptionState.disabled,
                onTap: () => _selectOption(i, question),
              ),
              const SizedBox(height: AppSpacing.sm),
            ],
            const SizedBox(height: AppSpacing.sm),
            if (_selectedOption != null)
              PrimaryButton(
                label: _currentIndex + 1 >= effectiveQuestions.length ? 'See Results' : 'Next',
                onPressed: () => _next(effectiveQuestions.length),
              ),
          ],
        );
      },
      loading: () => const Padding(
        padding: EdgeInsets.symmetric(vertical: AppSpacing.xxl),
        child: LoadingWidget(),
      ),
      error: (_, __) => ErrorStateWidget(
        onRetry: () => ref.invalidate(grammarQuestionsProvider(widget.lesson.id)),
      ),
    );
  }
}

enum _OptionState { neutral, correct, incorrect, disabled }

class _OptionTile extends StatelessWidget {
  const _OptionTile({required this.label, required this.state, required this.onTap});

  final String label;
  final _OptionState state;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    final (Color borderColor, Color? fillColor) = switch (state) {
      _OptionState.neutral => (colorScheme.outline, null),
      _OptionState.correct => (colorScheme.primary, colorScheme.primary.withValues(alpha: 0.08)),
      _OptionState.incorrect => (colorScheme.error, colorScheme.error.withValues(alpha: 0.08)),
      _OptionState.disabled => (colorScheme.outline, null),
    };

    return InkWell(
      onTap: state == _OptionState.neutral ? onTap : null,
      borderRadius: AppRadius.mdAll,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(AppSpacing.md),
        decoration: BoxDecoration(
          color: fillColor,
          borderRadius: AppRadius.mdAll,
          border: Border.all(color: borderColor, width: 1.5),
        ),
        child: Text(label, style: Theme.of(context).textTheme.bodyLarge),
      ),
    );
  }
}

class _QuizResult extends StatelessWidget {
  const _QuizResult({required this.correctCount, required this.total});

  final int correctCount;
  final int total;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text('Quiz complete!', style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: AppSpacing.sm),
        Text(
          'You got $correctCount out of $total correct.',
          style: Theme.of(context).textTheme.bodyLarge,
        ),
        const SizedBox(height: AppSpacing.lg),
        PrimaryButton(label: 'Done', onPressed: () => Navigator.of(context).pop()),
      ],
    );
  }
}
