import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:supabase_flutter/supabase_flutter.dart' as supabase;

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/router/onboarding_status_provider.dart';
import '../../../../shared/widgets/widgets.dart';
import '../widgets/onboarding_progress_dots.dart';

class _AudienceOption {
  const _AudienceOption(this.key, this.label, this.description, this.icon);
  final String key;
  final String label;
  final String description;
  final IconData icon;
}

class _GoalOption {
  const _GoalOption(this.key, this.label, this.description);
  final String key;
  final String label;
  final String description;
}

class _PlacementQuestion {
  const _PlacementQuestion({
    required this.id,
    required this.questionType,
    required this.skill,
    required this.cefrLevel,
    required this.difficultyRank,
    required this.prompt,
    required this.options,
    required this.sequenceNo,
  });

  final String id;
  final String questionType;
  final String skill;
  final String cefrLevel;
  final int difficultyRank;
  final String prompt;
  final List<String> options;
  final int sequenceNo;

  factory _PlacementQuestion.fromMap(Map<String, dynamic> map) {
    return _PlacementQuestion(
      id: map['id'] as String,
      questionType: map['question_type'] as String,
      skill: map['skill'] as String,
      cefrLevel: map['cefr_level'] as String,
      difficultyRank: (map['difficulty_rank'] as num).toInt(),
      prompt: map['prompt'] as String,
      options: (map['options'] as List?)?.map((e) => e.toString()).toList() ?? const [],
      sequenceNo: (map['sequence_no'] as num).toInt(),
    );
  }
}

const _audiences = <_AudienceOption>[
  _AudienceOption('student', 'Student', 'School, college, exams and everyday confidence', Icons.school_outlined),
  _AudienceOption('working_professional', 'Working Professional', 'Meetings, clients, presentations and career growth', Icons.work_outline),
  _AudienceOption('interview_prep', 'Job Seeker / Interview Prep', 'Interviews, workplace readiness and confidence', Icons.badge_outlined),
  _AudienceOption('homemaker', 'Homemaker', 'Family, shopping, school, banking and daily conversations', Icons.home_outlined),
  _AudienceOption('driver_delivery', 'Driver / Auto / Rickshaw / Delivery', 'Passengers, directions, payments and customer communication', Icons.local_taxi_outlined),
  _AudienceOption('retail_service', 'Shop / Retail / Service Worker', 'Customers, products, prices, complaints and service English', Icons.storefront_outlined),
  _AudienceOption('skilled_worker', 'Skilled Worker / Technician', 'Instructions, safety, tools, customers and job updates', Icons.handyman_outlined),
  _AudienceOption('business_owner', 'Business Owner / Entrepreneur', 'Sales, vendors, negotiation, networking and teams', Icons.business_center_outlined),
  _AudienceOption('general_learner', 'General English Learner', 'Everyday English from basic to advanced', Icons.language_outlined),
];

const _goalsByAudience = <String, List<_GoalOption>>{
  'student': [
    _GoalOption('school_college', 'School / College English', 'Classroom, campus and academic communication'),
    _GoalOption('exam_prep', 'Exam Preparation', 'Build English for exams and study'),
    _GoalOption('presentation_confidence', 'Presentation & Confidence', 'Speak clearly in front of others'),
    _GoalOption('general_fluency', 'General Fluency', 'Build overall speaking confidence'),
    _GoalOption('daily_english', 'Daily Conversation', 'Speak naturally in everyday situations'),
  ],
  'working_professional': [
    _GoalOption('business_english', 'Business English', 'Professional communication at work'),
    _GoalOption('workplace_english', 'Workplace English', 'Meetings, updates and daily workplace English'),
    _GoalOption('presentation_confidence', 'Presentation & Confidence', 'Present ideas clearly and confidently'),
    _GoalOption('general_fluency', 'General Fluency', 'Speak more naturally and confidently'),
    _GoalOption('interview_prep', 'Job Interview', 'Prepare for future interviews and growth'),
  ],
  'interview_prep': [
    _GoalOption('interview_prep', 'Job Interview', 'Prepare for interviews and job conversations'),
    _GoalOption('workplace_english', 'Workplace English', 'Get ready for workplace communication'),
    _GoalOption('general_fluency', 'General Fluency', 'Improve overall speaking confidence'),
    _GoalOption('presentation_confidence', 'Presentation & Confidence', 'Speak confidently under pressure'),
  ],
  'homemaker': [
    _GoalOption('daily_english', 'Daily Conversation', 'Speak naturally in everyday situations'),
    _GoalOption('general_fluency', 'General Fluency', 'Build confidence from basics upward'),
    _GoalOption('travel_english', 'Travel English', 'Travel, booking and directions'),
    _GoalOption('customer_communication', 'Customer Communication', 'Handle shops, services and phone calls'),
  ],
  'driver_delivery': [
    _GoalOption('customer_communication', 'Customer Communication', 'Passengers, customers and service conversations'),
    _GoalOption('daily_english', 'Daily Conversation', 'Everyday practical English'),
    _GoalOption('travel_english', 'Travel English', 'Directions, locations, stations and airports'),
    _GoalOption('general_fluency', 'General Fluency', 'Build confidence from basic to advanced'),
  ],
  'retail_service': [
    _GoalOption('customer_communication', 'Customer Communication', 'Serve customers clearly and politely'),
    _GoalOption('workplace_english', 'Workplace English', 'Daily job communication and instructions'),
    _GoalOption('daily_english', 'Daily Conversation', 'Practical everyday speaking'),
    _GoalOption('general_fluency', 'General Fluency', 'Build overall confidence'),
  ],
  'skilled_worker': [
    _GoalOption('workplace_english', 'Workplace English', 'Instructions, safety and job communication'),
    _GoalOption('customer_communication', 'Customer Communication', 'Speak clearly during customer visits'),
    _GoalOption('daily_english', 'Daily Conversation', 'Practical everyday speaking'),
    _GoalOption('general_fluency', 'General Fluency', 'Build overall confidence'),
  ],
  'business_owner': [
    _GoalOption('business_english', 'Business English', 'Sales, vendors, negotiation and teams'),
    _GoalOption('customer_communication', 'Customer Communication', 'Speak clearly with customers and clients'),
    _GoalOption('presentation_confidence', 'Presentation & Confidence', 'Pitch and present ideas confidently'),
    _GoalOption('general_fluency', 'General Fluency', 'Build natural confident communication'),
  ],
  'general_learner': [
    _GoalOption('general_fluency', 'General Fluency', 'Build overall speaking confidence'),
    _GoalOption('daily_english', 'Daily Conversation', 'Speak naturally in everyday situations'),
    _GoalOption('travel_english', 'Travel English', 'Travel, directions and booking'),
    _GoalOption('presentation_confidence', 'Presentation & Confidence', 'Speak confidently in public situations'),
  ],
};

class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  final _pageController = PageController();
  int _pageIndex = 0;
  String? _selectedAudience;
  String? _selectedGoal;
  bool _savingProfile = false;
  static const _totalPages = 4;

  void _goToPage(int index) {
    _pageController.animateToPage(index, duration: const Duration(milliseconds: 260), curve: Curves.easeOutCubic);
    setState(() => _pageIndex = index);
  }

  Future<void> _startPlacement() async {
    if (_selectedAudience == null || _selectedGoal == null || _savingProfile) return;
    setState(() => _savingProfile = true);
    try {
      final client = supabase.Supabase.instance.client;
      if (client.auth.currentUser == null) throw Exception('Please sign in again.');
      await client.rpc('accept_current_legal_documents', params: {'p_source': 'onboarding'});
      await client.rpc('save_my_onboarding_profile', params: {
        'p_audience_type': _selectedAudience,
        'p_goal': _selectedGoal,
        'p_native_language': 'hi',
      });
      if (!mounted) return;
      _goToPage(3);
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Could not save your learning profile. Please try again.')));
    } finally {
      if (mounted) setState(() => _savingProfile = false);
    }
  }

  void _finishOnboarding() {
    ref.read(onboardingCompleteProvider.notifier).markComplete();
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: AppSpacing.base),
            OnboardingProgressDots(count: _totalPages, currentIndex: _pageIndex),
            Expanded(
              child: PageView(
                controller: _pageController,
                physics: const NeverScrollableScrollPhysics(),
                onPageChanged: (index) => setState(() => _pageIndex = index),
                children: [
                  _WelcomePage(onNext: () => _goToPage(1)),
                  _AudiencePage(
                    selectedAudience: _selectedAudience,
                    onSelect: (value) => setState(() {
                      _selectedAudience = value;
                      _selectedGoal = null;
                    }),
                    onNext: () => _goToPage(2),
                  ),
                  _GoalPage(
                    audienceKey: _selectedAudience,
                    selectedGoal: _selectedGoal,
                    isLoading: _savingProfile,
                    onSelect: (value) => setState(() => _selectedGoal = value),
                    onNext: _startPlacement,
                    onBack: () => _goToPage(1),
                  ),
                  _PlacementTestPage(
                    audienceKey: _selectedAudience!,
                    goalKey: _selectedGoal!,
                    onComplete: _finishOnboarding,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _WelcomePage extends StatelessWidget {
  const _WelcomePage({required this.onNext});
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.xl),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 100,
            height: 100,
            decoration: BoxDecoration(
              gradient: LinearGradient(colors: [colors.primary, colors.secondary]),
              borderRadius: BorderRadius.circular(30),
              boxShadow: [BoxShadow(color: colors.primary.withValues(alpha: .22), blurRadius: 28, offset: const Offset(0, 12))],
            ),
            child: Icon(Icons.record_voice_over_outlined, color: colors.onPrimary, size: 46),
          ),
          const SizedBox(height: AppSpacing.xl),
          Text('Speak better English\nfor your real life.', textAlign: TextAlign.center, style: Theme.of(context).textTheme.displayLarge),
          const SizedBox(height: AppSpacing.sm),
          Text(
            'FluentX builds a personal path around who you are, your goal, and your current English level.',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: colors.onSurfaceVariant),
          ),
          const SizedBox(height: AppSpacing.xxl),
          PrimaryButton(label: 'Build My Learning Path', onPressed: onNext),
        ],
      ),
    );
  }
}

class _AudiencePage extends StatelessWidget {
  const _AudiencePage({required this.selectedAudience, required this.onSelect, required this.onNext});
  final String? selectedAudience;
  final ValueChanged<String> onSelect;
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.base),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Tell us about yourself', style: Theme.of(context).textTheme.displayLarge),
          const SizedBox(height: AppSpacing.xs),
          Text('Your lessons, vocabulary and AI roleplays will match your real life.', style: Theme.of(context).textTheme.bodyLarge),
          const SizedBox(height: AppSpacing.lg),
          Expanded(
            child: ListView.separated(
              itemCount: _audiences.length,
              separatorBuilder: (_, __) => const SizedBox(height: AppSpacing.sm),
              itemBuilder: (context, index) {
                final item = _audiences[index];
                return _ChoiceCard(
                  icon: item.icon,
                  title: item.label,
                  subtitle: item.description,
                  selected: selectedAudience == item.key,
                  onTap: () => onSelect(item.key),
                );
              },
            ),
          ),
          const SizedBox(height: AppSpacing.sm),
          PrimaryButton(label: 'Continue', isEnabled: selectedAudience != null, onPressed: selectedAudience == null ? null : onNext),
        ],
      ),
    );
  }
}

class _GoalPage extends StatelessWidget {
  const _GoalPage({required this.audienceKey, required this.selectedGoal, required this.isLoading, required this.onSelect, required this.onNext, required this.onBack});
  final String? audienceKey;
  final String? selectedGoal;
  final bool isLoading;
  final ValueChanged<String> onSelect;
  final VoidCallback onNext;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    final goals = _goalsByAudience[audienceKey] ?? const <_GoalOption>[];
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.base),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("What's your main goal?", style: Theme.of(context).textTheme.displayLarge),
          const SizedBox(height: AppSpacing.xs),
          Text("We'll personalize your complete A1–C1 path around this goal.", style: Theme.of(context).textTheme.bodyLarge),
          const SizedBox(height: AppSpacing.lg),
          Expanded(
            child: ListView.separated(
              itemCount: goals.length,
              separatorBuilder: (_, __) => const SizedBox(height: AppSpacing.sm),
              itemBuilder: (context, index) {
                final goal = goals[index];
                return _ChoiceCard(
                  icon: Icons.track_changes_outlined,
                  title: goal.label,
                  subtitle: goal.description,
                  selected: selectedGoal == goal.key,
                  onTap: () => onSelect(goal.key),
                );
              },
            ),
          ),
          Row(
            children: [
              Expanded(child: OutlinedButton(onPressed: isLoading ? null : onBack, child: const Text('Back'))),
              const SizedBox(width: AppSpacing.sm),
              Expanded(child: PrimaryButton(label: 'Start Level Check', isLoading: isLoading, isEnabled: selectedGoal != null, onPressed: selectedGoal == null ? null : onNext)),
            ],
          ),
        ],
      ),
    );
  }
}

class _ChoiceCard extends StatelessWidget {
  const _ChoiceCard({required this.icon, required this.title, required this.subtitle, required this.selected, required this.onTap});
  final IconData icon;
  final String title;
  final String subtitle;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(20),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.all(AppSpacing.base),
        decoration: BoxDecoration(
          color: selected ? colors.primaryContainer : colors.surface,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: selected ? colors.primary : colors.outlineVariant, width: selected ? 2 : 1),
          boxShadow: selected ? [BoxShadow(color: colors.primary.withValues(alpha: .10), blurRadius: 18, offset: const Offset(0, 8))] : null,
        ),
        child: Row(
          children: [
            CircleAvatar(backgroundColor: selected ? colors.primary : colors.surfaceContainerHighest, child: Icon(icon, color: selected ? colors.onPrimary : colors.onSurfaceVariant)),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
                const SizedBox(height: 4),
                Text(subtitle, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: colors.onSurfaceVariant)),
              ]),
            ),
            if (selected) Icon(Icons.check_circle_rounded, color: colors.primary),
          ],
        ),
      ),
    );
  }
}

class _PlacementTestPage extends StatefulWidget {
  const _PlacementTestPage({required this.audienceKey, required this.goalKey, required this.onComplete});
  final String audienceKey;
  final String goalKey;
  final VoidCallback onComplete;

  @override
  State<_PlacementTestPage> createState() => _PlacementTestPageState();
}

class _PlacementTestPageState extends State<_PlacementTestPage> {
  final _speech = stt.SpeechToText();
  final _client = supabase.Supabase.instance.client;

  List<_PlacementQuestion> _questions = const [];
  String? _attemptId;
  int _index = 0;
  int? _selectedIndex;
  bool _loading = true;
  bool _submitting = false;
  bool _listening = false;
  String _spokenText = '';
  String? _error;
  Map<String, dynamic>? _result;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final user = _client.auth.currentUser;
      if (user == null) throw Exception('Please sign in again.');
      final rows = await _client
          .from('placement_questions')
          .select('id,question_type,skill,cefr_level,difficulty_rank,prompt,options,sequence_no')
          .eq('is_active', true)
          .order('sequence_no');
      final questions = (rows as List).map((e) => _PlacementQuestion.fromMap(Map<String, dynamic>.from(e as Map))).toList();
      final attempt = await _client.from('placement_attempts').insert({'user_id': user.id}).select('id').single();
      if (!mounted) return;
      setState(() {
        _questions = questions;
        _attemptId = attempt['id'] as String;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = 'We could not start your level check. Please try again.';
      });
    }
  }

  Future<void> _saveMcqAndContinue() async {
    if (_selectedIndex == null || _attemptId == null || _submitting) return;
    setState(() => _submitting = true);
    try {
      final user = _client.auth.currentUser!;
      final q = _questions[_index];
      await _client.from('placement_answers').upsert({
        'attempt_id': _attemptId,
        'user_id': user.id,
        'question_id': q.id,
        'selected_index': _selectedIndex,
      }, onConflict: 'attempt_id,question_id');
      await _advance();
    } catch (_) {
      _showError('Could not save this answer. Please try again.');
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  Future<void> _toggleListening() async {
    if (_listening) {
      await _speech.stop();
      if (mounted) setState(() => _listening = false);
      return;
    }
    final available = await _speech.initialize();
    if (!available) {
      _showError('Speech recognition is unavailable on this device.');
      return;
    }
    setState(() {
      _spokenText = '';
      _listening = true;
    });
    await _speech.listen(
      listenFor: const Duration(seconds: 90),
      pauseFor: const Duration(seconds: 5),
      listenMode: stt.ListenMode.dictation,
      onResult: (result) {
        if (!mounted) return;
        setState(() => _spokenText = result.recognizedWords.trim());
      },
    );
  }

  Future<void> _scoreSpeakingAndContinue() async {
    if (_spokenText.trim().isEmpty || _attemptId == null || _submitting) return;
    setState(() => _submitting = true);
    try {
      await _speech.stop();
      if (mounted) setState(() => _listening = false);
      final q = _questions[_index];
      final response = await _client.functions.invoke('score-placement-speaking', body: {
        'attempt_id': _attemptId,
        'question_id': q.id,
        'spoken_text': _spokenText.trim(),
      });
      if (response.status < 200 || response.status >= 300) throw Exception('AI scoring failed');
      await _advance();
    } catch (_) {
      _showError('We could not score your speaking response. Please try again.');
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  Future<void> _advance() async {
    if (_index >= _questions.length - 1) {
      await _finishTest();
      return;
    }
    if (!mounted) return;
    setState(() {
      _index++;
      _selectedIndex = null;
      _spokenText = '';
    });
  }

  Future<void> _finishTest() async {
    final data = await _client.rpc('score_my_placement_attempt', params: {'p_attempt_id': _attemptId});
    Map<String, dynamic> result;
    if (data is List && data.isNotEmpty) {
      result = Map<String, dynamic>.from(data.first as Map);
    } else if (data is Map) {
      result = Map<String, dynamic>.from(data);
    } else {
      throw Exception('Invalid placement result');
    }
    if (!mounted) return;
    setState(() => _result = result);
  }

  void _showError(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  String _audienceLabel() => _audiences.firstWhere((e) => e.key == widget.audienceKey).label;
  String _goalLabel() => (_goalsByAudience[widget.audienceKey] ?? const <_GoalOption>[]).firstWhere((e) => e.key == widget.goalKey).label;

  @override
  void dispose() {
    _speech.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Padding(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          const Icon(Icons.cloud_off_outlined, size: 56),
          const SizedBox(height: AppSpacing.base),
          Text(_error!, textAlign: TextAlign.center),
          const SizedBox(height: AppSpacing.lg),
          PrimaryButton(label: 'Try Again', onPressed: () {
            setState(() {
              _error = null;
              _loading = true;
            });
            _load();
          }),
        ]),
      );
    }
    if (_result != null) return _buildResult(context);
    if (_questions.isEmpty) return const Center(child: Text('No placement questions are available.'));

    final q = _questions[_index];
    final progress = (_index + 1) / _questions.length;
    return Padding(
      padding: const EdgeInsets.fromLTRB(AppSpacing.base, AppSpacing.sm, AppSpacing.base, AppSpacing.base),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Text('Level Check', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
          const Spacer(),
          Text('${_index + 1}/${_questions.length}', style: Theme.of(context).textTheme.labelLarge),
        ]),
        const SizedBox(height: AppSpacing.sm),
        ClipRRect(borderRadius: BorderRadius.circular(99), child: LinearProgressIndicator(value: progress, minHeight: 8)),
        const SizedBox(height: AppSpacing.md),
        Wrap(spacing: 8, runSpacing: 8, children: [
          _Pill(label: q.cefrLevel),
          _Pill(label: q.skill.replaceAll('_', ' ').toUpperCase()),
          if (q.questionType == 'speaking') const _Pill(label: 'SPEAKING'),
        ]),
        const SizedBox(height: AppSpacing.lg),
        Text(q.questionType == 'speaking' ? 'Speak your answer' : 'Choose the best answer', style: Theme.of(context).textTheme.labelLarge),
        const SizedBox(height: AppSpacing.sm),
        Text(q.prompt, style: Theme.of(context).textTheme.headlineLarge?.copyWith(fontWeight: FontWeight.w800, height: 1.18)),
        const SizedBox(height: AppSpacing.lg),
        Expanded(child: q.questionType == 'speaking' ? _buildSpeaking(context, q) : _buildMcq(context, q)),
      ]),
    );
  }

  Widget _buildMcq(BuildContext context, _PlacementQuestion q) {
    return Column(children: [
      Expanded(
        child: ListView.separated(
          itemCount: q.options.length,
          separatorBuilder: (_, __) => const SizedBox(height: AppSpacing.sm),
          itemBuilder: (context, index) {
            final selected = _selectedIndex == index;
            return _AnswerCard(
              label: String.fromCharCode(65 + index),
              text: q.options[index],
              selected: selected,
              onTap: () => setState(() => _selectedIndex = index),
            );
          },
        ),
      ),
      const SizedBox(height: AppSpacing.sm),
      PrimaryButton(label: 'Continue', isLoading: _submitting, isEnabled: _selectedIndex != null, onPressed: _selectedIndex == null ? null : _saveMcqAndContinue),
    ]);
  }

  Widget _buildSpeaking(BuildContext context, _PlacementQuestion q) {
    final colors = Theme.of(context).colorScheme;
    return Column(children: [
      const Spacer(),
      InkWell(
        onTap: _toggleListening,
        borderRadius: BorderRadius.circular(100),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          width: 138,
          height: 138,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: _listening ? colors.primary : colors.primaryContainer,
            boxShadow: [BoxShadow(color: colors.primary.withValues(alpha: _listening ? .28 : .15), blurRadius: _listening ? 34 : 22, spreadRadius: _listening ? 8 : 2)],
          ),
          child: Icon(_listening ? Icons.stop_rounded : Icons.mic_rounded, size: 58, color: _listening ? colors.onPrimary : colors.primary),
        ),
      ),
      const SizedBox(height: AppSpacing.md),
      Text(_listening ? 'Listening… tap to stop' : 'Tap the mic and speak naturally', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
      const SizedBox(height: AppSpacing.sm),
      Container(
        width: double.infinity,
        constraints: const BoxConstraints(minHeight: 96),
        padding: const EdgeInsets.all(AppSpacing.base),
        decoration: BoxDecoration(color: colors.surfaceContainerLowest, borderRadius: BorderRadius.circular(18), border: Border.all(color: colors.outlineVariant)),
        child: Text(_spokenText.isEmpty ? 'Your speech will appear here…' : _spokenText, style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: _spokenText.isEmpty ? colors.onSurfaceVariant : colors.onSurface)),
      ),
      const Spacer(),
      PrimaryButton(label: 'Score My Speaking', isLoading: _submitting, isEnabled: _spokenText.trim().isNotEmpty, onPressed: _spokenText.trim().isEmpty ? null : _scoreSpeakingAndContinue),
    ]);
  }

  Widget _buildResult(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final level = (_result!['assigned_level'] ?? 'A1').toString();
    final score = double.tryParse((_result!['final_score'] ?? 0).toString()) ?? 0;
    final week = int.tryParse((_result!['start_week'] ?? 1).toString()) ?? 1;
    final subtitle = switch (level) {
      'A1' => 'Foundation',
      'A2' => 'Everyday Independence',
      'B1' => 'Independent Speaker',
      'B2' => 'Confident Communicator',
      'C1' => 'Advanced Communicator',
      _ => 'Foundation',
    };
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.xl),
      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        Container(
          width: 120,
          height: 120,
          decoration: BoxDecoration(shape: BoxShape.circle, gradient: LinearGradient(colors: [colors.primary, colors.secondary])),
          child: Center(child: Text(level, style: Theme.of(context).textTheme.displayMedium?.copyWith(color: colors.onPrimary, fontWeight: FontWeight.w900))),
        ),
        const SizedBox(height: AppSpacing.lg),
        Text('Your FluentX Level', style: Theme.of(context).textTheme.labelLarge),
        const SizedBox(height: 4),
        Text(subtitle, textAlign: TextAlign.center, style: Theme.of(context).textTheme.headlineLarge?.copyWith(fontWeight: FontWeight.w900)),
        const SizedBox(height: AppSpacing.base),
        Container(
          padding: const EdgeInsets.all(AppSpacing.base),
          decoration: BoxDecoration(color: colors.primaryContainer.withValues(alpha: .55), borderRadius: BorderRadius.circular(20)),
          child: Column(children: [
            _ResultRow(label: 'Placement score', value: '${score.round()}%'),
            const Divider(),
            _ResultRow(label: 'Your starting point', value: 'Week $week'),
            const Divider(),
            _ResultRow(label: 'Personalized for', value: _audienceLabel()),
            const Divider(),
            _ResultRow(label: 'Main goal', value: _goalLabel()),
          ]),
        ),
        const SizedBox(height: AppSpacing.base),
        Text('Your lessons, roleplays and weekly tests will now adapt to this starting level.', textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: colors.onSurfaceVariant)),
        const SizedBox(height: AppSpacing.xl),
        PrimaryButton(label: 'Start My Personalized Course', onPressed: widget.onComplete),
      ]),
    );
  }
}

class _Pill extends StatelessWidget {
  const _Pill({required this.label});
  final String label;
  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(color: colors.primaryContainer, borderRadius: BorderRadius.circular(999)),
      child: Text(label, style: Theme.of(context).textTheme.labelSmall?.copyWith(color: colors.primary, fontWeight: FontWeight.w800)),
    );
  }
}

class _AnswerCard extends StatelessWidget {
  const _AnswerCard({required this.label, required this.text, required this.selected, required this.onTap});
  final String label;
  final String text;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(18),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 160),
        padding: const EdgeInsets.all(AppSpacing.base),
        decoration: BoxDecoration(
          color: selected ? colors.primaryContainer : colors.surface,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: selected ? colors.primary : colors.outlineVariant, width: selected ? 2 : 1),
        ),
        child: Row(children: [
          Container(
            width: 38,
            height: 38,
            alignment: Alignment.center,
            decoration: BoxDecoration(shape: BoxShape.circle, color: selected ? colors.primary : colors.surfaceContainerHighest),
            child: Text(label, style: TextStyle(color: selected ? colors.onPrimary : colors.onSurface, fontWeight: FontWeight.w800)),
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(child: Text(text, style: Theme.of(context).textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w600))),
          if (selected) Icon(Icons.check_circle_rounded, color: colors.primary),
        ]),
      ),
    );
  }
}

class _ResultRow extends StatelessWidget {
  const _ResultRow({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Expanded(child: Text(label, style: Theme.of(context).textTheme.bodyMedium)),
        const SizedBox(width: 12),
        Flexible(child: Text(value, textAlign: TextAlign.right, style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w800))),
      ]),
    );
  }
}


class _OnboardingLegalPreview extends StatelessWidget {
  const _OnboardingLegalPreview({required this.title, required this.sections});
  final String title;
  final List<(String, String)> sections;
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(title)),
    body: ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: sections.length,
      separatorBuilder: (_, __) => const SizedBox(height: 18),
      itemBuilder: (context, index) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(sections[index].$1, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
        const SizedBox(height: 6),
        Text(sections[index].$2),
      ]),
    ),
  );
}
