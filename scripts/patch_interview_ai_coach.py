from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
target = root / 'lib/features/interview_prep/presentation/screens/interview_prep_screen.dart'
if not target.exists():
    raise SystemExit(f'Missing target: {target}')

target.write_text(r'''import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/network/supabase_provider.dart';
import '../../../../shared/widgets/widgets.dart';
import '../../../authentication/application/providers/auth_providers.dart';

class InterviewPrepScreen extends ConsumerStatefulWidget {
  const InterviewPrepScreen({super.key});

  @override
  ConsumerState<InterviewPrepScreen> createState() => _InterviewPrepScreenState();
}

class _InterviewPrepScreenState extends ConsumerState<InterviewPrepScreen> {
  final _answerController = TextEditingController();
  final _speech = stt.SpeechToText();

  List<Map<String, dynamic>> _questions = const [];
  String _category = 'HR Essentials';
  String? _attemptId;
  int _index = 0;
  bool _loading = true;
  bool _scoring = false;
  bool _listening = false;
  bool _showTip = false;
  Map<String, dynamic>? _result;
  final List<int> _scores = [];

  static const _categories = ['HR Essentials', 'Behavioral', 'Leadership'];

  @override
  void initState() {
    super.initState();
    _loadQuestions();
  }

  @override
  void dispose() {
    _answerController.dispose();
    _speech.stop();
    super.dispose();
  }

  Future<void> _loadQuestions() async {
    setState(() {
      _loading = true;
      _attemptId = null;
      _index = 0;
      _result = null;
      _scores.clear();
      _answerController.clear();
    });
    try {
      final client = ref.read(supabaseClientProvider);
      final rows = await client
          .from('interview_questions')
          .select('id,category,question,coaching_tip,sort_order')
          .eq('category', _category)
          .eq('is_active', true)
          .order('sort_order');
      if (!mounted) return;
      setState(() {
        _questions = List<Map<String, dynamic>>.from(rows);
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _loading = false);
    }
  }

  Future<bool> _ensureAttempt() async {
    if (_attemptId != null) return true;
    final user = ref.read(authStateChangesProvider).value;
    if (user == null) return false;
    try {
      final client = ref.read(supabaseClientProvider);
      final row = await client
          .from('interview_attempts')
          .insert({'user_id': user.id, 'category': _category})
          .select('id')
          .single();
      _attemptId = row['id'] as String?;
      return _attemptId != null;
    } catch (_) {
      return false;
    }
  }

  Future<void> _toggleMic() async {
    if (_listening) {
      await _speech.stop();
      if (mounted) setState(() => _listening = false);
      return;
    }

    final available = await _speech.initialize(
      onStatus: (status) {
        if (!mounted) return;
        if (status == 'done' || status == 'notListening') {
          setState(() => _listening = false);
        }
      },
      onError: (_) {
        if (mounted) setState(() => _listening = false);
      },
    );
    if (!available) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Microphone speech recognition is unavailable on this device.')),
        );
      }
      return;
    }

    setState(() => _listening = true);
    await _speech.listen(
      listenMode: stt.ListenMode.dictation,
      partialResults: true,
      onResult: (result) {
        _answerController.text = result.recognizedWords;
        _answerController.selection = TextSelection.collapsed(offset: _answerController.text.length);
        if (mounted) setState(() {});
      },
    );
  }

  Future<void> _scoreAnswer() async {
    final answer = _answerController.text.trim();
    if (answer.length < 10 || _questions.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please give a fuller answer before scoring.')),
      );
      return;
    }
    if (!await _ensureAttempt()) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not start interview practice. Please try again.')),
        );
      }
      return;
    }

    setState(() => _scoring = true);
    try {
      final client = ref.read(supabaseClientProvider);
      final response = await client.functions.invoke(
        'score-interview-answer',
        body: {
          'attempt_id': _attemptId,
          'question_id': _questions[_index]['id'],
          'answer_text': answer,
        },
      );
      final data = Map<String, dynamic>.from(response.data as Map);
      if (response.status >= 400 || data['error'] != null) {
        throw Exception(data['error'] ?? 'Scoring failed');
      }
      final score = (data['score'] as num?)?.round() ?? 0;
      if (mounted) {
        setState(() {
          _result = data;
          _scores.add(score);
        });
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('AI scoring is unavailable right now. Please try again.')),
        );
      }
    } finally {
      if (mounted) setState(() => _scoring = false);
    }
  }

  Future<void> _next() async {
    if (_index >= _questions.length - 1) {
      final client = ref.read(supabaseClientProvider);
      if (_attemptId != null) {
        final overall = _scores.isEmpty ? 0 : (_scores.reduce((a, b) => a + b) / _scores.length).round();
        try {
          await client.from('interview_attempts').update({
            'overall_score': overall,
            'completed_at': DateTime.now().toIso8601String(),
          }).eq('id', _attemptId!);
        } catch (_) {}
      }
      if (mounted) setState(() => _index = _questions.length);
      return;
    }

    setState(() {
      _index += 1;
      _result = null;
      _showTip = false;
      _answerController.clear();
    });
  }

  void _restart() {
    _loadQuestions();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('AI Interview Coach')),
      body: SafeArea(
        top: false,
        child: _loading
            ? const LoadingWidget()
            : _questions.isEmpty
                ? ErrorStateWidget(onRetry: _loadQuestions)
                : _index >= _questions.length
                    ? _buildComplete(context)
                    : _buildPractice(context),
      ),
    );
  }

  Widget _buildPractice(BuildContext context) {
    final q = _questions[_index];
    final progress = (_index + 1) / _questions.length;
    return ListView(
      padding: const EdgeInsets.all(AppSpacing.base),
      children: [
        Text('Choose interview type', style: Theme.of(context).textTheme.bodySmall),
        const SizedBox(height: AppSpacing.xs),
        Wrap(
          spacing: AppSpacing.sm,
          children: _categories.map((category) {
            return ChoiceChip(
              label: Text(category),
              selected: _category == category,
              onSelected: (_) {
                if (_category == category) return;
                setState(() => _category = category);
                _loadQuestions();
              },
            );
          }).toList(),
        ),
        const SizedBox(height: AppSpacing.lg),
        ClipRRect(
          borderRadius: BorderRadius.circular(100),
          child: LinearProgressIndicator(value: progress, minHeight: 7),
        ),
        const SizedBox(height: AppSpacing.sm),
        Text('Question ${_index + 1} of ${_questions.length}'),
        const SizedBox(height: AppSpacing.lg),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.record_voice_over_outlined, size: 30, color: Theme.of(context).colorScheme.primary),
              const SizedBox(height: AppSpacing.md),
              Text(q['question'] as String? ?? '', style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: AppSpacing.sm),
              TextButton.icon(
                onPressed: () => setState(() => _showTip = !_showTip),
                icon: const Icon(Icons.lightbulb_outline, size: 18),
                label: Text(_showTip ? 'Hide coaching tip' : 'Show coaching tip'),
              ),
              if (_showTip) Text(q['coaching_tip'] as String? ?? ''),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.lg),
        TextField(
          controller: _answerController,
          minLines: 5,
          maxLines: 10,
          decoration: InputDecoration(
            labelText: 'Your answer',
            hintText: 'Speak or type your interview answer here…',
            alignLabelWithHint: true,
            suffixIcon: IconButton(
              onPressed: _toggleMic,
              tooltip: _listening ? 'Stop listening' : 'Answer with microphone',
              icon: Icon(_listening ? Icons.stop_circle_outlined : Icons.mic_none_outlined),
            ),
          ),
        ),
        const SizedBox(height: AppSpacing.md),
        PrimaryButton(
          label: _result == null ? 'Score My Answer' : 'Score Again',
          isLoading: _scoring,
          onPressed: _scoring ? null : _scoreAnswer,
        ),
        if (_result != null) ...[
          const SizedBox(height: AppSpacing.lg),
          _buildResult(context, _result!),
          const SizedBox(height: AppSpacing.md),
          ElevatedButton.icon(
            onPressed: _next,
            icon: Icon(_index == _questions.length - 1 ? Icons.flag_outlined : Icons.arrow_forward),
            label: Text(_index == _questions.length - 1 ? 'Finish Interview' : 'Next Question'),
          ),
        ],
      ],
    );
  }

  Widget _buildResult(BuildContext context, Map<String, dynamic> data) {
    final score = (data['score'] as num?)?.round() ?? 0;
    final strengths = List<String>.from((data['strengths'] as List?) ?? const []);
    final improvements = List<String>.from((data['improvements'] as List?) ?? const []);
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text('$score/100', style: Theme.of(context).textTheme.headlineLarge),
              const Spacer(),
              const Icon(Icons.auto_awesome_outlined),
            ],
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(data['feedback'] as String? ?? ''),
          if (strengths.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.md),
            Text('What worked', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: AppSpacing.xs),
            for (final item in strengths) Text('• $item'),
          ],
          if (improvements.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.md),
            Text('Improve next', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: AppSpacing.xs),
            for (final item in improvements) Text('• $item'),
          ],
        ],
      ),
    );
  }

  Widget _buildComplete(BuildContext context) {
    final overall = _scores.isEmpty ? 0 : (_scores.reduce((a, b) => a + b) / _scores.length).round();
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: AppCard(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.workspace_premium_outlined, size: 54),
              const SizedBox(height: AppSpacing.md),
              Text('$overall/100', style: Theme.of(context).textTheme.displayLarge),
              const SizedBox(height: AppSpacing.sm),
              Text('Interview practice complete', style: Theme.of(context).textTheme.headlineSmall, textAlign: TextAlign.center),
              const SizedBox(height: AppSpacing.sm),
              Text('Your answers and AI coaching have been saved to your FluentX profile.', textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodyMedium),
              const SizedBox(height: AppSpacing.lg),
              ElevatedButton.icon(onPressed: _restart, icon: const Icon(Icons.replay), label: const Text('Practice Again')),
            ],
          ),
        ),
      ),
    );
  }
}
''', encoding='utf-8')
print(f'Updated {target}')
