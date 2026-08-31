from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')


def patch(path_rel: str, transform):
    path = root / path_rel
    if not path.exists():
        raise SystemExit(f'Missing target: {path_rel}')
    old = path.read_text(encoding='utf-8')
    new = transform(old)
    if new == old:
        print(f'No change needed: {path_rel}')
        return
    path.write_text(new, encoding='utf-8')
    print(f'Updated: {path_rel}')


# ---------------------------------------------------------------------------
# HOME: prevent an indefinitely-pending home provider from looking like a
# frozen app. After 6s show an interactive recovery state with retry and core
# navigation. Also make pull-to-refresh wait only a bounded amount of time.
# ---------------------------------------------------------------------------
def fix_home(text: str) -> str:
    if "import 'dart:async';" not in text:
        text = text.replace("import 'package:flutter/material.dart';", "import 'dart:async';\n\nimport 'package:flutter/material.dart';", 1)

    start = text.find('class HomeScreen extends ConsumerWidget {')
    end = text.find('class _HomeContent extends ConsumerWidget {')
    if start < 0 or end < 0:
        if 'class _HomeScreenState extends ConsumerState<HomeScreen>' in text:
            return text
        raise SystemExit('HomeScreen markers not found')

    replacement = r'''class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  Timer? _slowTimer;
  bool _showRecovery = false;

  @override
  void initState() {
    super.initState();
    _armSlowTimer();
  }

  @override
  void dispose() {
    _slowTimer?.cancel();
    super.dispose();
  }

  void _armSlowTimer() {
    _slowTimer?.cancel();
    _slowTimer = Timer(const Duration(seconds: 6), () {
      if (mounted) setState(() => _showRecovery = true);
    });
  }

  void _retryHome() {
    setState(() => _showRecovery = false);
    ref.invalidate(homeSummaryProvider);
    _armSlowTimer();
  }

  @override
  Widget build(BuildContext context) {
    final homeSummaryAsync = ref.watch(homeSummaryProvider);
    if (!homeSummaryAsync.isLoading) _slowTimer?.cancel();

    return Scaffold(
      body: SafeArea(
        child: homeSummaryAsync.when(
          data: (summary) => _HomeContent(summary: summary),
          loading: () => _showRecovery
              ? _HomeRecovery(onRetry: _retryHome)
              : const _HomeLoadingSkeleton(),
          error: (_, __) => _HomeRecovery(onRetry: _retryHome),
        ),
      ),
    );
  }
}

class _HomeRecovery extends StatelessWidget {
  const _HomeRecovery({required this.onRetry});
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(16, 18, 16, 120),
      children: [
        Row(children: [
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              gradient: LinearGradient(colors: [colors.primary, colors.tertiary]),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(Icons.auto_awesome_rounded, color: colors.onPrimary, size: 18),
          ),
          const SizedBox(width: 9),
          Text('Fluent X', style: Theme.of(context).textTheme.titleMedium?.copyWith(color: colors.primary, fontWeight: FontWeight.w900)),
        ]),
        const SizedBox(height: 28),
        AppCard(
          child: Column(children: [
            Icon(Icons.sync_rounded, size: 46, color: colors.primary),
            const SizedBox(height: 12),
            Text('Home is reconnecting', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 7),
            Text(
              'Your dashboard data is taking longer than expected. You can retry or continue using learning features.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: colors.onSurfaceVariant),
            ),
            const SizedBox(height: 16),
            FilledButton.icon(onPressed: onRetry, icon: const Icon(Icons.refresh_rounded), label: const Text('Retry Home')),
          ]),
        ),
        const SizedBox(height: 24),
        Text('Quick Actions', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
        const SizedBox(height: 10),
        const QuickActionGrid(),
        const SizedBox(height: 18),
        Row(children: [
          Expanded(child: FilledButton.tonalIcon(onPressed: () => context.push(RoutePaths.learn), icon: const Icon(Icons.school_outlined), label: const Text('Learn'))),
          const SizedBox(width: 10),
          Expanded(child: FilledButton.tonalIcon(onPressed: () => context.push(RoutePaths.progress), icon: const Icon(Icons.insights_outlined), label: const Text('Progress'))),
        ]),
      ],
    );
  }
}

'''
    text = text[:start] + replacement + text[end:]

    old_refresh = "      onRefresh: () async => ref.invalidate(homeSummaryProvider),"
    new_refresh = r'''      onRefresh: () async {
        ref.invalidate(homeSummaryProvider);
        await Future.any<void>([
          ref.read(homeSummaryProvider.future).then<void>((_) {}),
          Future<void>.delayed(const Duration(seconds: 5)),
        ]);
      },'''
    if old_refresh in text:
        text = text.replace(old_refresh, new_refresh, 1)
    return text


patch('lib/features/home/presentation/screens/home_screen.dart', fix_home)


# ---------------------------------------------------------------------------
# MAYA: bound every network request, start a local guided session if session
# creation is unavailable, submit speech when the speech plugin reports done,
# and keep voice mode listening after a guided reply. This eliminates silent
# hangs for both text and voice.
# ---------------------------------------------------------------------------
def fix_maya(text: str) -> str:
    # State used to avoid duplicate voice submissions from finalResult + status.
    field_marker = "  bool _speakerOn = true;\n"
    if 'bool _voiceSubmitInFlight = false;' not in text:
        if field_marker not in text:
            raise SystemExit('Maya state marker not found')
        text = text.replace(field_marker, field_marker + '  bool _voiceSubmitInFlight = false;\n', 1)

    # Make local coach respond naturally to the exact QA phrase and common typo.
    start = text.find('  String _localPracticeReply(String message) {')
    end = text.find('  int _limitForTier(String tier)', start)
    if start < 0 or end < 0:
        raise SystemExit('Maya local reply markers not found')
    local_reply = r'''  String _localPracticeReply(String message) {
    final clean = message.trim();
    final lower = clean.toLowerCase();
    final words = clean.split(RegExp(r'\s+')).where((w) => w.isNotEmpty).length;

    if (lower.contains('how are you')) {
      return 'Hi! I’m doing great, thank you 😊 How are you today? Try answering me in one complete English sentence.';
    }
    if (lower == 'hi' || lower == 'hii' || lower == 'hlo' ||
        lower == 'hello' || lower == 'hey' || lower.startsWith('hlo maya')) {
      return 'Hi! 😊 Nice to hear from you. How are you today? Tell me one thing you did today.';
    }
    if (lower.contains("what's up") || lower.contains('whats up') ||
        lower.contains('what s up') || lower.contains('what’s up') ||
        lower.contains('whats ap') || lower.contains("what's ap") || lower.contains('what’s ap')) {
      return 'Not much — I’m ready to practice English with you 😊 “What’s up?” is the natural phrase. What are you doing right now?';
    }
    if (lower.contains('thank')) {
      return 'You’re welcome! 😊 Now tell me what you would like to practice: daily conversation, work, travel, or pronunciation.';
    }
    if (words < 5) {
      return 'Good start. Make it a complete sentence and add one detail. I’ll keep the conversation going with you.';
    }
    if (clean.endsWith('?')) {
      return 'Good question. I’m listening. Now give your own answer in two complete English sentences and I’ll help improve it.';
    }
    return 'Nice! I understood you. Add one more detail — why, when, where, or how — and say the full idea naturally.';
  }

'''
    text = text[:start] + local_reply + text[end:]

    # Bound initial scenario loading so Maya home never spins forever.
    text = text.replace(
        ".from('ai_practice_scenarios')\n          .select('id,title,description,category,track,created_at')\n          .order('created_at');",
        ".from('ai_practice_scenarios')\n          .select('id,title,description,category,track,created_at')\n          .order('created_at')\n          .timeout(const Duration(seconds: 7));",
        1,
    )

    # Bound session insert and fall back to a local session instead of failing.
    old_insert = r'''      final row = await _client.from('ai_practice_sessions').insert({
        'user_id': user.id,
        'scenario_id': scenario['id'],
        'transcript': <Map<String, dynamic>>[],
      }).select('id').single();'''
    new_insert = r'''      final row = await _client.from('ai_practice_sessions').insert({
        'user_id': user.id,
        'scenario_id': scenario['id'],
        'transcript': <Map<String, dynamic>>[],
      }).select('id').single().timeout(const Duration(seconds: 7));'''
    if old_insert in text:
        text = text.replace(old_insert, new_insert, 1)

    old_start_catch = r'''    } catch (_) {
      if (!mounted) return;
      setState(() {
        _error = 'Could not start Maya conversation.';
        _sending = false;
        _voiceMode = false;
      });
    }
  }

  Future<void> _startFreeTalk'''
    new_start_catch = r'''    } catch (_) {
      if (!mounted) return;
      setState(() {
        _sessionId = 'local-${DateTime.now().millisecondsSinceEpoch}';
        _active = _localFreeTalkScenario();
        _error = 'AI service is reconnecting. Guided conversation is active.';
        _sending = false;
      });
      if (voice) {
        _startVoiceTimer();
        Future<void>.delayed(const Duration(milliseconds: 350), () async {
          if (mounted && _voiceMode && !_voicePaused && !_sending && !_listening) {
            await _toggleMic();
          }
        });
      }
    }
  }

  Future<void> _startFreeTalk'''
    if old_start_catch in text:
        text = text.replace(old_start_catch, new_start_catch, 1)
    elif "Guided conversation is active." not in text:
        raise SystemExit('Maya start catch marker not found')

    # Add helper to submit captured speech exactly once.
    toggle_marker = '  Future<void> _toggleMic() async {'
    helper = r'''  Future<void> _submitCapturedSpeech() async {
    if (_voiceSubmitInFlight || _sending || _voicePaused) return;
    final captured = _liveWords.trim();
    if (captured.isEmpty) {
      if (mounted) setState(() => _listening = false);
      return;
    }
    _voiceSubmitInFlight = true;
    if (mounted) {
      setState(() {
        _listening = false;
        _liveWords = '';
      });
    }
    try {
      await _send(captured);
    } finally {
      _voiceSubmitInFlight = false;
    }
  }

'''
    if '_submitCapturedSpeech() async' not in text:
        pos = text.find(toggle_marker)
        if pos < 0:
            raise SystemExit('Maya toggle mic marker not found')
        text = text[:pos] + helper + text[pos:]

    # Replace speech init with status/error-aware initialization.
    old_init = r'''    await _tts.stop();
    final ok = await _speech.initialize();
    if (!ok) {
      if (mounted) setState(() => _error = 'Microphone speech recognition is unavailable.');
      return;
    }'''
    new_init = r'''    await _tts.stop();
    final ok = await _speech.initialize(
      onStatus: (status) {
        if (!mounted) return;
        if ((status == 'done' || status == 'notListening') && _listening) {
          Future<void>.microtask(_submitCapturedSpeech);
        }
      },
      onError: (_) {
        if (!mounted) return;
        if (_liveWords.trim().isNotEmpty) {
          Future<void>.microtask(_submitCapturedSpeech);
        } else {
          setState(() {
            _listening = false;
            _error = 'I could not hear that clearly. Tap the mic and try again.';
          });
        }
      },
    );
    if (!ok) {
      if (mounted) setState(() => _error = 'Microphone speech recognition is unavailable.');
      return;
    }'''
    if old_init in text:
        text = text.replace(old_init, new_init, 1)
    elif 'onStatus: (status)' not in text:
        raise SystemExit('Maya speech init marker not found')

    # Manual stop should submit whatever has already been recognized.
    old_stop = r'''    if (_listening) {
      await _speech.stop();
      if (mounted) setState(() => _listening = false);
      final text = _liveWords.trim();
      if (text.isNotEmpty) await _send(text);
      return;
    }'''
    new_stop = r'''    if (_listening) {
      await _speech.stop();
      await _submitCapturedSpeech();
      return;
    }'''
    if old_stop in text:
        text = text.replace(old_stop, new_stop, 1)

    # finalResult and status can both fire; route through the guarded helper.
    old_on_speech = r'''  void _onSpeech(SpeechRecognitionResult result) {
    if (!mounted) return;
    setState(() => _liveWords = result.recognizedWords);
    if (result.finalResult) {
      final text = result.recognizedWords.trim();
      setState(() => _listening = false);
      if (text.isNotEmpty) _send(text);
    }
  }'''
    new_on_speech = r'''  void _onSpeech(SpeechRecognitionResult result) {
    if (!mounted) return;
    setState(() => _liveWords = result.recognizedWords);
    if (result.finalResult) {
      Future<void>.microtask(_submitCapturedSpeech);
    }
  }'''
    if old_on_speech in text:
        text = text.replace(old_on_speech, new_on_speech, 1)
    elif 'Future<void>.microtask(_submitCapturedSpeech);' not in text:
        raise SystemExit('Maya speech result marker not found')

    # Network AI reply must never hang forever.
    old_invoke = r'''      final response = await _client.functions.invoke('ai-practice-chat', body: {
        'action': 'reply',
        'session_id': _sessionId,
        'user_message': clean,
      });'''
    new_invoke = r'''      final response = await _client.functions.invoke('ai-practice-chat', body: {
        'action': 'reply',
        'session_id': _sessionId,
        'user_message': clean,
      }).timeout(const Duration(seconds: 10));'''
    if old_invoke in text:
        text = text.replace(old_invoke, new_invoke, 1)
    elif ").timeout(const Duration(seconds: 10));" not in text:
        raise SystemExit('Maya reply invoke marker not found')

    # Local replies should also continue hands-free voice conversation.
    old_local_return = r'''      _scrollDown();
      if (_speakerOn) await _speak(reply, 'en-IN', 'encouraging');
      return;
    }
    try {'''
    new_local_return = r'''      _scrollDown();
      if (_speakerOn) await _speak(reply, 'en-IN', 'encouraging');
      if (_voiceMode && !_voicePaused && mounted) {
        await Future<void>.delayed(const Duration(milliseconds: 300));
        if (_voiceMode && !_voicePaused && !_sending && !_listening && mounted) {
          await _toggleMic();
        }
      }
      return;
    }
    try {'''
    if old_local_return in text:
        text = text.replace(old_local_return, new_local_return, 1)

    # Summarize should also have a timeout, so End cannot hang.
    text = text.replace(
        "      final response = await _client.functions.invoke('ai-practice-chat', body: {\n        'action': 'summarize',\n        'session_id': _sessionId,\n      });",
        "      final response = await _client.functions.invoke('ai-practice-chat', body: {\n        'action': 'summarize',\n        'session_id': _sessionId,\n      }).timeout(const Duration(seconds: 8));",
        1,
    )

    return text


patch('lib/features/ai_practice/presentation/screens/ai_practice_hub_screen.dart', fix_maya)

print('Home + Maya reliability v3 applied successfully.')
