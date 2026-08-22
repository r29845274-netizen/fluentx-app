from pathlib import Path
import shutil
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
repo_root = Path(__file__).resolve().parent.parent

src_avatar = repo_root / 'scripts/assets/maya_tutor.jpg'
dst_avatar = root / 'assets/images/maya_tutor.jpg'
if not src_avatar.exists():
    raise SystemExit(f'Maya avatar asset not found: {src_avatar}')
dst_avatar.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(src_avatar, dst_avatar)

screen = root / 'lib/features/ai_practice/presentation/screens/ai_practice_hub_screen.dart'
screen.parent.mkdir(parents=True, exist_ok=True)
screen.write_text(r'''import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_recognition_result.dart';
import 'package:speech_to_text/speech_to_text.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class AiPracticeHubScreen extends StatefulWidget {
  const AiPracticeHubScreen({super.key});
  @override
  State<AiPracticeHubScreen> createState() => _AiPracticeHubScreenState();
}

class _Turn {
  const _Turn(this.role, this.text);
  final String role;
  final String text;
}

class _AiPracticeHubScreenState extends State<AiPracticeHubScreen> {
  final _speech = SpeechToText();
  final _tts = FlutterTts();
  final _scroll = ScrollController();
  final List<_Turn> _turns = [];
  List<Map<String, dynamic>> _scenarios = [];
  Map<String, dynamic>? _active;
  String? _sessionId;
  String? _suggestedEnglish;
  String? _correction;
  String _expression = 'calm';
  String _tier = 'free';
  String? _error;
  bool _loading = true;
  bool _sending = false;
  bool _listening = false;
  String _liveWords = '';

  SupabaseClient get _client => Supabase.instance.client;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _speech.stop();
    _tts.stop();
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final user = _client.auth.currentUser;
      final rows = await _client
          .from('ai_practice_scenarios')
          .select('id,title,description,category,track,created_at')
          .order('created_at');
      var tier = 'free';
      if (user != null) {
        try {
          final sub = await _client
              .from('user_subscription_access')
              .select('tier,entitlement_active')
              .eq('user_id', user.id)
              .maybeSingle();
          if (sub != null && sub['entitlement_active'] == true) {
            tier = (sub['tier'] ?? 'free').toString();
          }
        } catch (_) {}
      }
      final scenarios = List<Map<String, dynamic>>.from(rows);
      scenarios.sort((a, b) {
        final af = _isFreeTalk(a) ? 0 : 1;
        final bf = _isFreeTalk(b) ? 0 : 1;
        return af.compareTo(bf);
      });
      if (!mounted) return;
      setState(() {
        _scenarios = scenarios;
        _tier = tier;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  bool _isFreeTalk(Map<String, dynamic> s) {
    final title = (s['title'] ?? '').toString().toLowerCase();
    final track = (s['track'] ?? '').toString().toLowerCase();
    return title.contains('free') || track == 'free_talk';
  }

  String get _limitLabel => switch (_tier) {
        'annual' => '24 hours/day',
        'monthly' => '6 hours/day',
        _ => '1 hour/day',
      };

  String get _planLabel => switch (_tier) {
        'annual' => 'Elite Annual',
        'monthly' => 'Pro Monthly',
        _ => 'Free',
      };

  Future<void> _start(Map<String, dynamic> scenario) async {
    final user = _client.auth.currentUser;
    if (user == null) {
      setState(() => _error = 'Please sign in to talk with Maya.');
      return;
    }
    setState(() {
      _sending = true;
      _error = null;
      _turns.clear();
      _suggestedEnglish = null;
      _correction = null;
      _expression = 'calm';
    });
    try {
      final row = await _client.from('ai_practice_sessions').insert({
        'user_id': user.id,
        'scenario_id': scenario['id'],
        'transcript': <Map<String, dynamic>>[],
      }).select('id').single();
      if (!mounted) return;
      setState(() {
        _sessionId = row['id'].toString();
        _active = scenario;
        _sending = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() { _error = 'Could not start Maya conversation.'; _sending = false; });
    }
  }

  Future<void> _toggleMic() async {
    if (_sending || _sessionId == null) return;
    if (_listening) {
      await _speech.stop();
      if (mounted) setState(() => _listening = false);
      final text = _liveWords.trim();
      if (text.isNotEmpty) await _send(text);
      return;
    }
    final ok = await _speech.initialize();
    if (!ok) {
      if (mounted) setState(() => _error = 'Microphone speech recognition is unavailable.');
      return;
    }
    setState(() { _listening = true; _liveWords = ''; _error = null; });
    await _speech.listen(
      onResult: _onSpeech,
      listenFor: const Duration(minutes: 2),
      pauseFor: const Duration(seconds: 3),
      partialResults: true,
      cancelOnError: true,
    );
  }

  void _onSpeech(SpeechRecognitionResult result) {
    if (!mounted) return;
    setState(() => _liveWords = result.recognizedWords);
    if (result.finalResult) {
      final text = result.recognizedWords.trim();
      setState(() => _listening = false);
      if (text.isNotEmpty) _send(text);
    }
  }

  Future<void> _send(String text) async {
    if (_sessionId == null || text.trim().isEmpty || _sending) return;
    final clean = text.trim();
    setState(() {
      _turns.add(_Turn('user', clean));
      _sending = true;
      _suggestedEnglish = null;
      _correction = null;
      _liveWords = '';
      _error = null;
    });
    _scrollDown();
    try {
      final response = await _client.functions.invoke('ai-practice-chat', body: {
        'action': 'reply',
        'session_id': _sessionId,
        'user_message': clean,
      });
      final data = response.data is Map
          ? Map<String, dynamic>.from(response.data as Map)
          : <String, dynamic>{};
      if (data['error'] != null) throw Exception(data['error']);
      final reply = (data['reply'] ?? '').toString().trim();
      if (!mounted) return;
      setState(() {
        if (reply.isNotEmpty) _turns.add(_Turn('assistant', reply));
        _suggestedEnglish = _nullableText(data['suggested_english']);
        _correction = _nullableText(data['correction']);
        _expression = _safeExpression(data['expression']);
        _sending = false;
      });
      _scrollDown();
      if (reply.isNotEmpty) {
        await _speak(reply, (data['tts_locale'] ?? 'en-IN').toString(), _expression);
      }
    } catch (e) {
      if (!mounted) return;
      final raw = e.toString();
      setState(() {
        _error = raw.contains('limit')
            ? 'Your AI Conversation time for today is complete. It resets daily.'
            : 'Maya could not reply right now. Please try again.';
        _sending = false;
      });
    }
  }

  String? _nullableText(dynamic value) {
    final text = value?.toString().trim() ?? '';
    return text.isEmpty ? null : text;
  }

  String _safeExpression(dynamic value) {
    const allowed = {'calm','happy','cool','encouraging','empathetic','thoughtful','playful','focused'};
    final v = value?.toString() ?? 'calm';
    return allowed.contains(v) ? v : 'calm';
  }

  Future<void> _speak(String text, String locale, String expression) async {
    await _tts.stop();
    await _tts.setLanguage(locale == 'hi-IN' ? 'hi-IN' : 'en-IN');
    double rate = .46;
    double pitch = 1.0;
    switch (expression) {
      case 'happy': rate = .50; pitch = 1.06; break;
      case 'playful': rate = .52; pitch = 1.08; break;
      case 'cool': rate = .47; pitch = 1.00; break;
      case 'focused': rate = .44; pitch = .98; break;
      case 'thoughtful': rate = .42; pitch = .97; break;
      case 'empathetic': rate = .40; pitch = .96; break;
      case 'encouraging': rate = .48; pitch = 1.04; break;
      default: rate = .44; pitch = 1.0;
    }
    await _tts.setSpeechRate(rate);
    await _tts.setPitch(pitch);
    await _tts.setVolume(1.0);
    await _tts.speak(text);
  }

  Future<void> _end() async {
    if (_sessionId == null) return _closeConversation();
    setState(() => _sending = true);
    try {
      final response = await _client.functions.invoke('ai-practice-chat', body: {
        'action': 'summarize', 'session_id': _sessionId,
      });
      final data = response.data is Map
          ? Map<String, dynamic>.from(response.data as Map)
          : <String, dynamic>{};
      if (!mounted) return;
      setState(() => _sending = false);
      await showModalBottomSheet<void>(
        context: context,
        useSafeArea: true,
        isScrollControlled: true,
        builder: (_) => _SummarySheet(data: data),
      );
    } catch (_) {
      if (mounted) setState(() => _sending = false);
    }
    _closeConversation();
  }

  void _closeConversation() {
    _speech.stop();
    _tts.stop();
    if (!mounted) return;
    setState(() {
      _active = null;
      _sessionId = null;
      _turns.clear();
      _suggestedEnglish = null;
      _correction = null;
      _expression = 'calm';
      _error = null;
    });
  }

  void _scrollDown() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent,
            duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    if (_active != null) return _conversationView();
    return _homeView();
  }

  Widget _homeView() {
    return Scaffold(
      appBar: AppBar(title: const Text('AI Conversation')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _hero(),
            const SizedBox(height: 20),
            if (_error != null) _errorBox(),
            Text('Talk with Maya', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
            const SizedBox(height: 4),
            const Text('Choose a situation, or start Free Talk and discuss almost anything while improving your English.'),
            const SizedBox(height: 12),
            ..._scenarios.map(_scenarioCard),
          ],
        ),
      ),
    );
  }

  Widget _hero() {
    final colors = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: [colors.primaryContainer, colors.secondaryContainer]),
        borderRadius: BorderRadius.circular(22),
      ),
      child: Row(children: [
        _MayaAvatar(size: 86, expression: 'happy'),
        const SizedBox(width: 14),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('Meet Maya', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
          const SizedBox(height: 2),
          const Text('Your natural AI English conversation coach'),
          const SizedBox(height: 8),
          const Text('Speak English, Hindi or Hinglish. Maya helps you express your thought naturally in English and keeps the conversation moving.'),
          const SizedBox(height: 8),
          Text('$_planLabel · $_limitLabel', style: const TextStyle(fontWeight: FontWeight.w800)),
        ])),
      ]),
    );
  }

  Widget _scenarioCard(Map<String, dynamic> s) {
    final free = _isFreeTalk(s);
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Card(
        elevation: free ? 1.5 : .2,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: _sending ? null : () => _start(s),
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Row(children: [
              CircleAvatar(child: Icon(free ? Icons.auto_awesome_rounded : Icons.forum_outlined)),
              const SizedBox(width: 12),
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(free ? 'Free Talk with Maya' : (s['title'] ?? '').toString(),
                    style: const TextStyle(fontWeight: FontWeight.w800)),
                const SizedBox(height: 3),
                Text(free
                    ? 'Talk about coding, news, finance, shopping, jokes, travel, work, hobbies and more.'
                    : (s['description'] ?? '').toString()),
              ])),
              const Icon(Icons.chevron_right),
            ]),
          ),
        ),
      ),
    );
  }

  Widget _conversationView() {
    final free = _active != null && _isFreeTalk(_active!);
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(Icons.close), onPressed: _closeConversation),
        titleSpacing: 0,
        title: Row(children: [
          _MayaAvatar(size: 38, expression: _expression),
          const SizedBox(width: 9),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Maya', style: TextStyle(fontWeight: FontWeight.w800)),
            Text(free ? 'Free Talk' : (_active?['title'] ?? '').toString(),
                maxLines: 1, overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.labelSmall),
          ])),
        ]),
        actions: [TextButton(onPressed: _sending ? null : _end, child: const Text('End'))],
      ),
      body: SafeArea(
        top: false,
        child: Column(children: [
          Container(
            width: double.infinity,
            margin: const EdgeInsets.fromLTRB(14, 8, 14, 0),
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.primaryContainer.withValues(alpha: .55),
              borderRadius: BorderRadius.circular(14),
            ),
            child: const Text('Hindi/Hinglish is welcome. Maya will show you how to say the same thought naturally in English and encourage you to retry.'),
          ),
          Expanded(child: _turns.isEmpty ? _starter(free) : _chatList()),
          if (_suggestedEnglish != null) _learningCard('You can say', _suggestedEnglish!, Icons.translate_rounded),
          if (_correction != null) _learningCard('Quick improvement', _correction!, Icons.auto_fix_high_rounded),
          if (_error != null) Padding(padding: const EdgeInsets.symmetric(horizontal: 14), child: _errorBox()),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 14),
            child: Column(children: [
              Text('$_planLabel · $_limitLabel · resets daily', style: Theme.of(context).textTheme.labelSmall),
              const SizedBox(height: 8),
              if (_liveWords.isNotEmpty)
                Padding(padding: const EdgeInsets.only(bottom: 8), child: Text('“$_liveWords”', textAlign: TextAlign.center)),
              if (_sending)
                const Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                  SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)),
                  SizedBox(width: 9), Text('Maya is thinking…'),
                ])
              else
                FilledButton.icon(
                  style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(52)),
                  onPressed: _toggleMic,
                  icon: Icon(_listening ? Icons.stop_circle_outlined : Icons.mic_rounded),
                  label: Text(_listening ? 'Tap to send' : 'Speak with Maya'),
                ),
            ]),
          ),
        ]),
      ),
    );
  }

  Widget _starter(bool free) {
    return Center(child: SingleChildScrollView(
      padding: const EdgeInsets.all(28),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        _MayaAvatar(size: 108, expression: 'happy'),
        const SizedBox(height: 14),
        Text('Hi, I’m Maya 👋', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
        const SizedBox(height: 8),
        Text(
          free
              ? 'Talk to me about anything. If you start in Hindi or Hinglish, I’ll help you say it naturally in English.'
              : 'Let’s practice “${_active?['title']}”. Start in English, Hindi or Hinglish — I’ll help you keep moving toward natural English.',
          textAlign: TextAlign.center,
        ),
      ]),
    ));
  }

  Widget _chatList() {
    return ListView.builder(
      controller: _scroll,
      padding: const EdgeInsets.all(14),
      itemCount: _turns.length,
      itemBuilder: (_, i) {
        final t = _turns[i];
        final mine = t.role == 'user';
        return Align(
          alignment: mine ? Alignment.centerRight : Alignment.centerLeft,
          child: Container(
            constraints: const BoxConstraints(maxWidth: 320),
            margin: const EdgeInsets.only(bottom: 9),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
            decoration: BoxDecoration(
              color: mine ? Theme.of(context).colorScheme.primary : Theme.of(context).colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Text(t.text, style: TextStyle(color: mine ? Theme.of(context).colorScheme.onPrimary : null)),
          ),
        );
      },
    );
  }

  Widget _learningCard(String title, String text, IconData icon) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.fromLTRB(14, 0, 14, 8),
      padding: const EdgeInsets.all(11),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.secondaryContainer.withValues(alpha: .55),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(icon, size: 20), const SizedBox(width: 9),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
          const SizedBox(height: 2), Text(text),
        ])),
      ]),
    );
  }

  Widget _errorBox() => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(10),
    decoration: BoxDecoration(color: Theme.of(context).colorScheme.errorContainer, borderRadius: BorderRadius.circular(12)),
    child: Text(_error ?? '', textAlign: TextAlign.center),
  );
}

class _MayaAvatar extends StatelessWidget {
  const _MayaAvatar({required this.size, required this.expression});
  final double size;
  final String expression;

  String get _emoji => switch (expression) {
        'happy' => '😊',
        'cool' => '😎',
        'encouraging' => '🌟',
        'empathetic' => '🤍',
        'thoughtful' => '🤔',
        'playful' => '😄',
        'focused' => '🎯',
        _ => '🙂',
      };

  @override
  Widget build(BuildContext context) {
    final primary = Theme.of(context).colorScheme.primary;
    return SizedBox(
      width: size + 8,
      height: size + 8,
      child: Stack(clipBehavior: Clip.none, children: [
        AnimatedContainer(
          duration: const Duration(milliseconds: 280),
          width: size,
          height: size,
          padding: const EdgeInsets.all(3),
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(color: primary.withValues(alpha: .7), width: 2.5),
            boxShadow: [BoxShadow(color: primary.withValues(alpha: .18), blurRadius: 14)],
          ),
          child: ClipOval(child: Image.asset('assets/images/maya_tutor.jpg', fit: BoxFit.cover)),
        ),
        Positioned(
          right: 0,
          bottom: 0,
          child: Container(
            padding: const EdgeInsets.all(3),
            decoration: BoxDecoration(color: Theme.of(context).colorScheme.surface, shape: BoxShape.circle),
            child: Text(_emoji, style: TextStyle(fontSize: size * .24)),
          ),
        ),
      ]),
    );
  }
}

class _SummarySheet extends StatelessWidget {
  const _SummarySheet({required this.data});
  final Map<String, dynamic> data;
  @override
  Widget build(BuildContext context) {
    final score = data['accuracy_score'] ?? 0;
    final notes = (data['fluency_notes'] ?? 'Nice practice. Keep speaking regularly.').toString();
    final corrections = data['corrected_sentences'] is List ? data['corrected_sentences'] as List : const [];
    return Padding(
      padding: EdgeInsets.fromLTRB(20, 20, 20, 20 + MediaQuery.of(context).viewPadding.bottom),
      child: SingleChildScrollView(child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
        Text('Conversation complete', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
        const SizedBox(height: 8),
        Text('English accuracy · $score%', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
        const SizedBox(height: 8), Text(notes),
        if (corrections.isNotEmpty) ...[
          const SizedBox(height: 14),
          const Text('Useful corrections', style: TextStyle(fontWeight: FontWeight.w800)),
          const SizedBox(height: 6),
          ...corrections.take(3).map((c) {
            final m = c is Map ? Map<String, dynamic>.from(c) : <String, dynamic>{};
            return Padding(padding: const EdgeInsets.only(bottom: 6), child: Text('• ${(m['corrected'] ?? '').toString()}'));
          }),
        ],
        const SizedBox(height: 16),
        FilledButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Done')),
      ])),
    );
  }
}
''', encoding='utf-8')

print('Maya AI Conversation fully applied: Free Talk, Hindi/Hinglish→English coaching, adaptive expression UI, emotional TTS, daily tier labels, summary and behavior protection compatibility.')