from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
path = root / 'lib/features/onboarding/presentation/screens/onboarding_screen.dart'
if not path.exists():
    raise SystemExit(f'Onboarding screen not found: {path}')

code = r'''import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart' as supabase;

import '../../../../core/constants/app_spacing.dart';
import '../../../../shared/widgets/widgets.dart';
import '../../application/providers/onboarding_providers.dart';
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

class _DiagnosticQuestion {
  const _DiagnosticQuestion(this.text, this.options, this.correctIndex);
  final String text;
  final List<String> options;
  final int correctIndex;
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

const _diagnosticQuestions = [
  _DiagnosticQuestion('She ___ to the office every day.', ['go', 'goes', 'going', 'gone'], 1),
  _DiagnosticQuestion('I have been working here ___ three years.', ['since', 'for', 'from', 'during'], 1),
  _DiagnosticQuestion('Could you tell me ___ the meeting starts?', ['when does', 'when', 'what time does', 'time'], 1),
];

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
  int _diagnosticIndex = 0;
  int? _selectedOption;
  int _correctCount = 0;
  bool _isSubmitting = false;
  static const _totalPages = 4;

  void _goToPage(int index) {
    _pageController.animateToPage(index, duration: const Duration(milliseconds: 250), curve: Curves.easeOutCubic);
    setState(() => _pageIndex = index);
  }

  Future<void> _finish() async {
    if (_selectedAudience == null || _selectedGoal == null || _isSubmitting) return;
    setState(() => _isSubmitting = true);
    try {
      final client = supabase.Supabase.instance.client;
      if (client.auth.currentUser == null) throw Exception('Please sign in again.');
      await client.rpc('save_my_onboarding_profile', params: {
        'p_audience_type': _selectedAudience,
        'p_goal': _selectedGoal,
        'p_native_language': 'hi',
      });
      if (!mounted) return;
      ref.read(onboardingCompleteProvider.notifier).markComplete();
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not save your learning profile. Please try again.')),
      );
      setState(() => _isSubmitting = false);
    }
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
                    onSelect: (value) => setState(() => _selectedGoal = value),
                    onNext: () => _goToPage(3),
                    onBack: () => _goToPage(1),
                  ),
                  _DiagnosticPage(
                    questionIndex: _diagnosticIndex,
                    selectedOption: _selectedOption,
                    correctCount: _correctCount,
                    isSubmitting: _isSubmitting,
                    onSelectOption: (index) {
                      if (_selectedOption != null) return;
                      setState(() {
                        _selectedOption = index;
                        if (index == _diagnosticQuestions[_diagnosticIndex].correctIndex) _correctCount++;
                      });
                    },
                    onNextQuestion: () => setState(() {
                      _diagnosticIndex++;
                      _selectedOption = null;
                    }),
                    onFinish: _finish,
                    onSkip: _finish,
                    onBack: () => _goToPage(2),
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
            width: 96,
            height: 96,
            decoration: BoxDecoration(color: colors.primary, borderRadius: BorderRadius.circular(24)),
            child: Icon(Icons.chat_outlined, color: colors.onPrimary, size: 44),
          ),
          const SizedBox(height: AppSpacing.xl),
          Text('AI-Powered\nEnglish Learning', textAlign: TextAlign.center, style: Theme.of(context).textTheme.displayLarge),
          const SizedBox(height: AppSpacing.sm),
          Text(
            'Your English journey will match who you are, why you want English, and your current level.',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: colors.onSurfaceVariant),
          ),
          const SizedBox(height: AppSpacing.xxl),
          PrimaryButton(label: 'Get Started', onPressed: onNext),
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
          Text('We’ll build examples, roleplays and vocabulary around your real life.', style: Theme.of(context).textTheme.bodyLarge),
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
  const _GoalPage({required this.audienceKey, required this.selectedGoal, required this.onSelect, required this.onNext, required this.onBack});
  final String? audienceKey;
  final String? selectedGoal;
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
          Text("We’ll personalize your 60-week path around this goal.", style: Theme.of(context).textTheme.bodyLarge),
          const SizedBox(height: AppSpacing.lg),
          Expanded(
            child: ListView.separated(
              itemCount: goals.length,
              separatorBuilder: (_, __) => const SizedBox(height: AppSpacing.sm),
              itemBuilder: (context, index) {
                final goal = goals[index];
                return _ChoiceCard(
                  icon: Icons.gps_fixed,
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
              Expanded(child: OutlinedButton(onPressed: onBack, child: const Text('Back'))),
              const SizedBox(width: AppSpacing.sm),
              Expanded(child: PrimaryButton(label: 'Continue', isEnabled: selectedGoal != null, onPressed: selectedGoal == null ? null : onNext)),
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
      borderRadius: BorderRadius.circular(18),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.all(AppSpacing.base),
        decoration: BoxDecoration(
          color: selected ? colors.primaryContainer : colors.surface,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: selected ? colors.primary : colors.outlineVariant, width: selected ? 2 : 1),
        ),
        child: Row(
          children: [
            CircleAvatar(backgroundColor: selected ? colors.primary : colors.surfaceContainerHighest, child: Icon(icon, color: selected ? colors.onPrimary : colors.onSurfaceVariant)),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                  const SizedBox(height: 4),
                  Text(subtitle, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: colors.onSurfaceVariant)),
                ],
              ),
            ),
            if (selected) Icon(Icons.check_circle, color: colors.primary),
          ],
        ),
      ),
    );
  }
}

class _DiagnosticPage extends StatelessWidget {
  const _DiagnosticPage({
    required this.questionIndex,
    required this.selectedOption,
    required this.correctCount,
    required this.isSubmitting,
    required this.onSelectOption,
    required this.onNextQuestion,
    required this.onFinish,
    required this.onSkip,
    required this.onBack,
  });
  final int questionIndex;
  final int? selectedOption;
  final int correctCount;
  final bool isSubmitting;
  final ValueChanged<int> onSelectOption;
  final VoidCallback onNextQuestion;
  final VoidCallback onFinish;
  final VoidCallback onSkip;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    if (questionIndex >= _diagnosticQuestions.length) {
      return Padding(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.celebration, size: 56, color: colors.primary),
            const SizedBox(height: AppSpacing.base),
            Text("You're all set!", style: Theme.of(context).textTheme.displayLarge),
            const SizedBox(height: AppSpacing.sm),
            Text('You got $correctCount of ${_diagnosticQuestions.length} right. We’ll use a full placement test in the next onboarding upgrade.', textAlign: TextAlign.center),
            const SizedBox(height: AppSpacing.xxl),
            PrimaryButton(label: 'Start Learning', isLoading: isSubmitting, onPressed: onFinish),
          ],
        ),
      );
    }

    final q = _diagnosticQuestions[questionIndex];
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.base),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Quick check ${questionIndex + 1} of ${_diagnosticQuestions.length}', style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: AppSpacing.sm),
          Text(q.text, style: Theme.of(context).textTheme.headlineLarge),
          const SizedBox(height: AppSpacing.lg),
          for (var i = 0; i < q.options.length; i++) ...[
            _ChoiceCard(
              icon: i == q.correctIndex && selectedOption != null ? Icons.check : Icons.circle_outlined,
              title: q.options[i],
              subtitle: '',
              selected: selectedOption == i,
              onTap: selectedOption == null ? () => onSelectOption(i) : () {},
            ),
            const SizedBox(height: AppSpacing.sm),
          ],
          const Spacer(),
          if (selectedOption != null)
            PrimaryButton(label: 'Next', onPressed: onNextQuestion)
          else
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                TextButton(onPressed: onBack, child: const Text('Back')),
                TextButton(onPressed: onSkip, child: const Text('Skip quick check')),
              ],
            ),
        ],
      ),
    );
  }
}
'''

path.write_text(code)
print('Personalized onboarding UI patch applied.')
