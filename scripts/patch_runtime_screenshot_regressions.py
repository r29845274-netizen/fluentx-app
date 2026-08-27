from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
if not (root / 'lib').exists():
    raise SystemExit(f'Flutter source not found: {root}')

changed = []

def patch(path_rel: str, transform):
    path = root / path_rel
    if not path.exists():
        raise SystemExit(f'Missing runtime file: {path_rel}')
    old = path.read_text(encoding='utf-8')
    new = transform(old)
    if new != old:
        path.write_text(new, encoding='utf-8')
        changed.append(path_rel)

# ---------------------------------------------------------------------------
# 1) Grammar: live DB can temporarily return an empty question set. The
#    screenshot showed multiple lessons opening to an empty sheet. Keep the
#    remote questions as the source of truth, but provide a small curriculum-
#    accurate local fallback for the affected shipped lessons.
# ---------------------------------------------------------------------------
def fix_grammar(text: str) -> str:
    marker = "  Future<void> _selectOption(int index, GrammarQuestion question) async {"
    helper = r'''  List<GrammarQuestion> _fallbackQuestions(GrammarLesson lesson) {
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

'''
    if '_fallbackQuestions(GrammarLesson lesson)' not in text:
        if marker not in text:
            raise SystemExit('Grammar fallback insertion marker not found')
        text = text.replace(marker, helper + marker, 1)

    old = """      data: (questions) {
        if (questions.isEmpty) {
          return const EmptyStateWidget(title: 'No questions yet for this lesson');
        }
        if (_currentIndex >= questions.length) {
          return _QuizResult(correctCount: _correctCount, total: questions.length);
        }

        final question = questions[_currentIndex];
"""
    new = """      data: (questions) {
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
"""
    if old in text:
        text = text.replace(old, new, 1)
        text = text.replace("'Question ${_currentIndex + 1} of ${questions.length}'", "'Question ${_currentIndex + 1} of ${effectiveQuestions.length}'", 1)
        text = text.replace("_currentIndex + 1 >= questions.length ? 'See Results' : 'Next'", "_currentIndex + 1 >= effectiveQuestions.length ? 'See Results' : 'Next'", 1)
        text = text.replace("onPressed: () => _next(questions.length),", "onPressed: () => _next(effectiveQuestions.length),", 1)
    elif 'final effectiveQuestions = questions.isEmpty' not in text:
        raise SystemExit('Grammar empty-state replacement marker not found')
    return text

patch('lib/features/grammar/presentation/widgets/grammar_quiz_sheet.dart', fix_grammar)

# ---------------------------------------------------------------------------
# 2) Writing: never leak raw server maps/errors into learner UI. The remote AI
#    call remains retryable; users get a clean actionable message if Gemini/
#    Edge Function is temporarily unavailable.
# ---------------------------------------------------------------------------
def fix_writing(text: str) -> str:
    old = """          Text(
            controllerState.error is Failure
                ? (controllerState.error! as Failure).uiMessage
                : 'Something went wrong while scoring your writing.',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: colorScheme.error),
          ),
"""
    new = """          Text(
            'AI feedback is temporarily unavailable. Your text is still here — please tap Submit again in a moment.',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: colorScheme.error),
          ),
"""
    if old in text:
        text = text.replace(old, new, 1)
    elif 'AI feedback is temporarily unavailable.' not in text:
        raise SystemExit('Writing error marker not found')
    return text

patch('lib/features/writing/presentation/widgets/writing_editor_sheet.dart', fix_writing)

# ---------------------------------------------------------------------------
# 3) Pronunciation: fix the exact RenderFlex overflow shown in the screenshot.
#    Dropdown uses full available width, and custom sentence controls stack on
#    narrow phones instead of forcing a horizontal row.
# ---------------------------------------------------------------------------
def fix_pronunciation(text: str) -> str:
    marker = """            DropdownButtonFormField<String>(
              value: _phrases.contains(_target) ? _target : null,
"""
    replacement = """            DropdownButtonFormField<String>(
              isExpanded: true,
              value: _phrases.contains(_target) ? _target : null,
"""
    if marker in text:
        text = text.replace(marker, replacement, 1)
    elif 'DropdownButtonFormField<String>(\n              isExpanded: true,' not in text:
        raise SystemExit('Pronunciation dropdown marker not found')

    old_row = """            Row(children: [
              Expanded(child: TextField(
                controller: _custom,
                maxLength: 180,
                decoration: const InputDecoration(border: OutlineInputBorder(), labelText: 'Or type your own sentence', counterText: ''),
              )),
              const SizedBox(width: 8),
              FilledButton.tonal(onPressed: _useCustom, child: const Text('Use')),
            ]),
"""
    new_row = """            LayoutBuilder(
              builder: (context, constraints) {
                final field = TextField(
                  controller: _custom,
                  maxLength: 180,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    labelText: 'Or type your own sentence',
                    counterText: '',
                  ),
                );
                if (constraints.maxWidth < 430) {
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      field,
                      const SizedBox(height: 8),
                      FilledButton.tonal(onPressed: _useCustom, child: const Text('Use sentence')),
                    ],
                  );
                }
                return Row(children: [
                  Expanded(child: field),
                  const SizedBox(width: 8),
                  FilledButton.tonal(onPressed: _useCustom, child: const Text('Use')),
                ]);
              },
            ),
"""
    if old_row in text:
        text = text.replace(old_row, new_row, 1)
    elif 'constraints.maxWidth < 430' not in text:
        raise SystemExit('Pronunciation custom-input marker not found')
    return text

patch('lib/features/learn/presentation/screens/pronunciation_practice_screen.dart', fix_pronunciation)

# ---------------------------------------------------------------------------
# 4) Progress + achievements: backend/RPC failure should not turn whole areas
#    into a generic broken screen. Keep Retry but show useful zero-state UI.
# ---------------------------------------------------------------------------
def fix_progress(text: str) -> str:
    old = """              error: (_, __) => ErrorStateWidget(
                onRetry: () => ref.invalidate(communicationDnaProvider),
              ),
"""
    new = """              error: (_, __) => AppCard(
                child: Column(
                  children: [
                    Icon(Icons.insights_outlined, size: 42, color: colorScheme.primary),
                    const SizedBox(height: AppSpacing.sm),
                    Text('Your Communication DNA is building', style: textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
                    const SizedBox(height: AppSpacing.xs),
                    const Text('Complete speaking, grammar and writing practice to generate your skill profile.', textAlign: TextAlign.center),
                    const SizedBox(height: AppSpacing.md),
                    OutlinedButton.icon(
                      onPressed: () => ref.invalidate(communicationDnaProvider),
                      icon: const Icon(Icons.refresh_rounded),
                      label: const Text('Refresh'),
                    ),
                  ],
                ),
              ),
"""
    if old in text:
        text = text.replace(old, new, 1)
    elif 'Your Communication DNA is building' not in text:
        raise SystemExit('Progress error marker not found')
    return text

patch('lib/features/progress/presentation/screens/progress_screen.dart', fix_progress)

def fix_achievements(text: str) -> str:
    old = """          error: (_, __) => ErrorStateWidget(
            onRetry: () => ref.invalidate(achievementStatsProvider),
          ),
"""
    new = """          error: (_, __) => ListView(
            padding: const EdgeInsets.all(AppSpacing.xl),
            children: [
              AppCard(
                child: Column(
                  children: [
                    Icon(Icons.emoji_events_outlined, size: 48, color: Theme.of(context).colorScheme.primary),
                    const SizedBox(height: AppSpacing.md),
                    Text('Achievements are syncing', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
                    const SizedBox(height: AppSpacing.sm),
                    const Text('Your completed activities are safe. Refresh to load the latest badges and milestones.', textAlign: TextAlign.center),
                    const SizedBox(height: AppSpacing.md),
                    FilledButton.tonalIcon(
                      onPressed: () => ref.invalidate(achievementStatsProvider),
                      icon: const Icon(Icons.refresh_rounded),
                      label: const Text('Refresh achievements'),
                    ),
                  ],
                ),
              ),
            ],
          ),
"""
    if old in text:
        text = text.replace(old, new, 1)
    elif 'Achievements are syncing' not in text:
        raise SystemExit('Achievements error marker not found')
    return text

patch('lib/features/achievements/presentation/screens/achievements_screen.dart', fix_achievements)

# ---------------------------------------------------------------------------
# 5) Premium: RevenueCat stream can remain pending forever when the test build
#    has no valid public SDK key/network response. Replace endless spinner after
#    8 seconds with a retryable, explicit billing state.
# ---------------------------------------------------------------------------
def fix_premium(text: str) -> str:
    state_marker = "class _PremiumScreenState extends ConsumerState<PremiumScreen> {\n  String? _selectedPackageId;"
    state_new = "class _PremiumScreenState extends ConsumerState<PremiumScreen> {\n  String? _selectedPackageId;\n  bool _billingTimedOut = false;"
    if state_marker in text:
        text = text.replace(state_marker, state_new, 1)
    elif 'bool _billingTimedOut = false;' not in text:
        raise SystemExit('Premium state marker not found')

    features_marker = "  static const _features = ["
    methods = r'''  @override
  void initState() {
    super.initState();
    _armBillingTimeout();
  }

  void _armBillingTimeout() {
    Future<void>.delayed(const Duration(seconds: 8), () {
      if (mounted) setState(() => _billingTimedOut = true);
    });
  }

  void _retryBilling() {
    setState(() => _billingTimedOut = false);
    ref.invalidate(subscriptionStatusProvider);
    ref.invalidate(premiumPackagesProvider);
    _armBillingTimeout();
  }

'''
    if 'void _armBillingTimeout()' not in text:
        if features_marker not in text:
            raise SystemExit('Premium methods marker not found')
        text = text.replace(features_marker, methods + features_marker, 1)

    build_marker = """    ref.listen(purchaseControllerProvider, (previous, next) {
"""
    timeout_block = """    if (subscriptionAsync.isLoading && _billingTimedOut) {
      return Scaffold(
        appBar: AppBar(title: const Text('Fluent X Premium')),
        body: SafeArea(
          child: Center(
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.xl),
              child: AppCard(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.storefront_outlined, size: 48, color: colorScheme.primary),
                    const SizedBox(height: AppSpacing.md),
                    Text('Google Play plans are taking too long to load', textAlign: TextAlign.center, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
                    const SizedBox(height: AppSpacing.sm),
                    const Text('Check your connection and try again. The app will no longer stay on an endless loading spinner.', textAlign: TextAlign.center),
                    const SizedBox(height: AppSpacing.lg),
                    FilledButton.icon(onPressed: _retryBilling, icon: const Icon(Icons.refresh_rounded), label: const Text('Retry plans')),
                  ],
                ),
              ),
            ),
          ),
        ),
      );
    }

"""
    if 'Google Play plans are taking too long to load' not in text:
        if build_marker not in text:
            raise SystemExit('Premium build marker not found')
        text = text.replace(build_marker, timeout_block + build_marker, 1)
    return text

patch('lib/features/premium/presentation/screens/premium_screen.dart', fix_premium)

# ---------------------------------------------------------------------------
# 6) Certificates: backend may provide blank display_title. Derive meaningful
#    visible names and force readable title contrast. Also finish Fluent X brand.
# ---------------------------------------------------------------------------
def fix_certificates(text: str) -> str:
    old = """                    final milestone = (row['milestone'] ?? '').toString();
                    final title = (row['display_title'] ?? milestone).toString();
"""
    new = """                    final milestone = (row['milestone'] ?? '').toString().trim();
                    final rawTitle = (row['display_title'] ?? '').toString().trim();
                    final title = rawTitle.isNotEmpty
                        ? rawTitle
                        : switch (milestone.toUpperCase()) {
                            'A1' => 'A1 Foundation Certificate',
                            'A2' => 'A2 Elementary Certificate',
                            'B1' => 'B1 Intermediate Certificate',
                            'B2' => 'B2 Upper-Intermediate Certificate',
                            'C1' => 'C1 Advanced Certificate',
                            'MASTER' => 'Communication Mastery Certificate',
                            _ => required >= 60 ? 'Communication Mastery Certificate' : 'Level Completion Certificate',
                          };
"""
    if old in text:
        text = text.replace(old, new, 1)
    elif 'A1 Foundation Certificate' not in text:
        raise SystemExit('Certificate title marker not found')
    text = text.replace(
        "Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),",
        "Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800, color: colors.onSurface)),",
    )
    text = text.replace("pw.Text('FLUENTX'", "pw.Text('FLUENT X'")
    text = text.replace("'FluentX Learner'", "'Fluent X Learner'")
    text = text.replace("'FluentX Completion Certificate'", "'Fluent X Completion Certificate'")
    return text

patch('lib/features/certificates/presentation/screens/certificates_screen.dart', fix_certificates)

# ---------------------------------------------------------------------------
# 7) Maya: if scenario table/RLS is unavailable, keep a clearly identified
#    guided practice fallback instead of blocking the whole feature. Real AI is
#    still used first whenever the live backend works. Also fix dark-theme text
#    on the white hero buttons.
# ---------------------------------------------------------------------------
def fix_maya(text: str) -> str:
    scenarios_line = "      final scenarios = List<Map<String, dynamic>>.from(rows);"
    scenarios_new = """      final scenarios = List<Map<String, dynamic>>.from(rows);
      if (scenarios.isEmpty) {
        scenarios.add(_localFreeTalkScenario());
      }"""
    if scenarios_line in text and '_localFreeTalkScenario());' not in text:
        text = text.replace(scenarios_line, scenarios_new, 1)

    catch_old = """    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = 'Maya could not load right now.';
        _loading = false;
      });
    }
  }

  int _limitForTier(String tier) => switch (tier) {
"""
    catch_new = """    } catch (_) {
      if (!mounted) return;
      setState(() {
        _scenarios = [_localFreeTalkScenario()];
        _error = null;
        _loading = false;
      });
    }
  }

  Map<String, dynamic> _localFreeTalkScenario() => <String, dynamic>{
        'id': 'local-free-talk',
        'title': 'Free Talk with Maya',
        'description': 'Guided English practice that stays available when the AI service is reconnecting.',
        'category': 'conversation',
        'track': 'free_talk',
      };

  bool _isLocalScenario(Map<String, dynamic> scenario) => scenario['id'] == 'local-free-talk';

  String _localPracticeReply(String message) {
    final words = message.trim().split(RegExp(r'\\s+')).where((w) => w.isNotEmpty).length;
    if (words < 5) {
      return 'Guided practice (offline): Good start. Say the same idea again with one reason or example.';
    }
    if (message.trim().endsWith('?')) {
      return 'Guided practice (offline): Nice question. Now answer it yourself in two complete English sentences.';
    }
    return 'Guided practice (offline): Well done. Add one more detail, then try saying the full answer naturally.';
  }

  int _limitForTier(String tier) => switch (tier) {
"""
    if catch_old in text:
        text = text.replace(catch_old, catch_new, 1)
    elif '_localFreeTalkScenario() =>' not in text:
        raise SystemExit('Maya load fallback marker not found')

    start_try = """    try {
      final row = await _client.from('ai_practice_sessions').insert({
"""
    start_new = """    try {
      if (_isLocalScenario(scenario)) {
        if (!mounted) return;
        setState(() {
          _sessionId = 'local-${DateTime.now().millisecondsSinceEpoch}';
          _active = scenario;
          _sending = false;
        });
        if (voice) {
          _startVoiceTimer();
          Future<void>.delayed(const Duration(milliseconds: 300), () async {
            if (mounted && _voiceMode && !_voicePaused && !_sending && !_listening) {
              await _toggleMic();
            }
          });
        }
        return;
      }
      final row = await _client.from('ai_practice_sessions').insert({
"""
    if start_try in text and "_sessionId = 'local-" not in text:
        text = text.replace(start_try, start_new, 1)

    send_marker = """    _scrollDown();
    try {
      final response = await _client.functions.invoke('ai-practice-chat', body: {
"""
    send_new = """    _scrollDown();
    if (_sessionId!.startsWith('local-')) {
      final reply = _localPracticeReply(clean);
      if (!mounted) return;
      setState(() {
        _turns.add(_Turn('assistant', reply));
        _sending = false;
      });
      _scrollDown();
      if (_speakerOn) await _speak(reply, 'en-IN', 'encouraging');
      return;
    }
    try {
      final response = await _client.functions.invoke('ai-practice-chat', body: {
"""
    if send_marker in text and "_sessionId!.startsWith('local-')" not in text:
        text = text.replace(send_marker, send_new, 1)

    # Avoid trying server summarize for local guided sessions.
    end_marker = """    if (_sessionId == null) {
      _closeConversation();
      return;
    }
    setState(() => _sending = true);
"""
    end_new = """    if (_sessionId == null || _sessionId!.startsWith('local-')) {
      _closeConversation();
      return;
    }
    setState(() => _sending = true);
"""
    if end_marker in text:
        text = text.replace(end_marker, end_new, 1)

    text = text.replace(
        "Text('Start a Conversation', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),",
        "Text('Start a Conversation', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900, color: Theme.of(context).colorScheme.onSurface)),",
        1,
    )
    text = text.replace(
        "Text(title, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 12)),\n              Text(subtitle, style: const TextStyle(fontSize: 11)),",
        "Text(title, style: const TextStyle(color: Color(0xFF17131F), fontWeight: FontWeight.w900, fontSize: 12)),\n              Text(subtitle, style: const TextStyle(color: Color(0xFF5D566B), fontSize: 11, fontWeight: FontWeight.w600)),",
        1,
    )
    return text

patch('lib/features/ai_practice/presentation/screens/ai_practice_hub_screen.dart', fix_maya)

print('Runtime screenshot regressions fixed:')
for item in changed:
    print(' -', item)
