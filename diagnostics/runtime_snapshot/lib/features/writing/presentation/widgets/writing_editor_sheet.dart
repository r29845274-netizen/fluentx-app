import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/app_radius.dart';
import '../../../../core/constants/app_spacing.dart';
import '../../../../core/error/failures.dart';
import '../../../../shared/widgets/widgets.dart';
import '../../application/providers/writing_providers.dart';
import '../../domain/entities/writing_prompt.dart';

class WritingEditorSheet extends ConsumerStatefulWidget {
  const WritingEditorSheet({required this.prompt, super.key});

  final WritingPrompt prompt;

  @override
  ConsumerState<WritingEditorSheet> createState() => _WritingEditorSheetState();
}

class _WritingEditorSheetState extends ConsumerState<WritingEditorSheet> {
  final _controller = TextEditingController();
  int _wordCount = 0;

  @override
  void initState() {
    super.initState();
    _controller.addListener(() {
      final words = _controller.text.trim();
      setState(() {
        _wordCount = words.isEmpty ? 0 : words.split(RegExp(r'\s+')).length;
      });
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final controllerState = ref.watch(writingControllerProvider);
    final colorScheme = Theme.of(context).colorScheme;

    if (controllerState.hasValue && controllerState.value != null) {
      return _ScoreResult(submission: controllerState.value!);
    }

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(widget.prompt.instructions, style: Theme.of(context).textTheme.bodyMedium),
        const SizedBox(height: AppSpacing.base),
        TextField(
          controller: _controller,
          maxLines: 8,
          minLines: 6,
          enabled: !controllerState.isLoading,
          decoration: InputDecoration(
            hintText: 'Start writing here…',
            alignLabelWithHint: true,
          ),
        ),
        const SizedBox(height: AppSpacing.xs),
        Align(
          alignment: Alignment.centerRight,
          child: Text('$_wordCount words', style: Theme.of(context).textTheme.labelSmall),
        ),
        if (controllerState.hasError) ...[
          const SizedBox(height: AppSpacing.sm),
          Text(
            controllerState.error is Failure
                ? (controllerState.error! as Failure).uiMessage
                : 'Something went wrong while scoring your writing.',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: colorScheme.error),
          ),
        ],
        const SizedBox(height: AppSpacing.base),
        PrimaryButton(
          label: 'Submit for AI Feedback',
          isLoading: controllerState.isLoading,
          onPressed: _wordCount < 10
              ? null
              : () => ref.read(writingControllerProvider.notifier).submitAndScore(
                    promptId: widget.prompt.id,
                    content: _controller.text.trim(),
                  ),
        ),
        if (_wordCount < 10) ...[
          const SizedBox(height: AppSpacing.xs),
          Text(
            'Write at least 10 words to get feedback.',
            style: Theme.of(context).textTheme.labelSmall,
          ),
        ],
      ],
    );
  }
}

class _ScoreResult extends StatelessWidget {
  const _ScoreResult({required this.submission});

  final WritingSubmission submission;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('AI Feedback', style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: AppSpacing.xs),
        Text(
          'AI-generated learning feedback. Review important communication before relying on it.',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(color: colorScheme.onSurfaceVariant),
        ),
        const SizedBox(height: AppSpacing.base),
        _ScoreBar(label: 'Grammar', value: submission.grammarScore ?? 0),
        _ScoreBar(label: 'Clarity', value: submission.clarityScore ?? 0),
        _ScoreBar(label: 'Structure', value: submission.structureScore ?? 0),
        _ScoreBar(label: 'Tone', value: submission.toneScore ?? 0),
        if (submission.aiFeedback != null) ...[
          const SizedBox(height: AppSpacing.base),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(AppSpacing.base),
            decoration: BoxDecoration(
              color: colorScheme.surfaceContainerHighest,
              borderRadius: AppRadius.mdAll,
            ),
            child: Text(submission.aiFeedback!, style: Theme.of(context).textTheme.bodyMedium),
          ),
        ],
        const SizedBox(height: AppSpacing.lg),
        PrimaryButton(label: 'Done', onPressed: () => Navigator.of(context).pop()),
      ],
    );
  }
}

class _ScoreBar extends StatelessWidget {
  const _ScoreBar({required this.label, required this.value});

  final String label;
  final int value;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label, style: Theme.of(context).textTheme.bodyMedium),
              Text('$value/100', style: Theme.of(context).textTheme.bodySmall),
            ],
          ),
          const SizedBox(height: 4),
          ClipRRect(
            borderRadius: BorderRadius.circular(100),
            child: LinearProgressIndicator(
              value: value / 100,
              minHeight: 6,
              backgroundColor: colorScheme.outline,
              valueColor: AlwaysStoppedAnimation<Color>(colorScheme.primary),
            ),
          ),
        ],
      ),
    );
  }
}
