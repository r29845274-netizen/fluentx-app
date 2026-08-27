import 'dart:async';

import 'package:flutter/material.dart';
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
  final _text = TextEditingController();
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
  bool _voiceMode = false;
  bool _voicePaused = false;
  bool _speakerOn = true;
  String _liveWords = '';
  int _voiceElapsed = 0;
  int _usedSeconds = 0;
  int _dailyLimitSeconds = 3600;
  Timer? _voiceTimer;

  SupabaseClient get _client => Supabase.instance.client;

  @override
  void initState() {
    super.initState();
    _tts.awaitSpeakCompletion(true);
    _load();
  }

  @override
  void dispose() {
    _voiceTimer?.cancel();
    _speech.stop();
    _tts.stop();
    _scroll.dispose();
    _text.dispose();
    super.dispose();
  }

  String _indiaDate() {
    final now = DateTime.now().toUtc().add(const Duration(hours: 5, minutes: 30));
    String two(int v) => v.toString().padLeft(2, '0');
    return '${now.year}-${two(now.month)}-${two(now.day)}';
  }

  Future<void> _load() async {
    try {
      final user = _client.auth.currentUser;
      final rows = await _client
          .from('ai_practice_scenarios')
          .select('id,title,description,category,track,created_at')
          .order('created_at');

      var tier = 'free';
      var used = 0;
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
        try {
          final usageRows = await _client
              .from('ai_practice_sessions')
              .select('billable_seconds')
              .eq('user_id', user.id)
              .eq('usage_date', _indiaDate());
          for (final row in List<Map<String, dynamic>>.from(usageRows)) {
            used += int.tryParse((row['billable_seconds'] ?? 0).toString()) ?? 0;
          }
        } catch (_) {}
      }

      final scenarios = List<Map<String, dynamic>>.from(rows);
      if (scenarios.isEmpty) {
        scenarios.add(_localFreeTalkScenario());
      }
      scenarios.sort((a, b) {
        final af = _isFreeTalk(a) ? 0 : 1;
        final bf = _isFreeTalk(b) ? 0 : 1;
        return af.compareTo(bf);
      });
      if (!mounted) return;
      setState(() {
        _scenarios = scenarios;
        _tier = tier;
        _dailyLimitSeconds = _limitForTier(tier);
        _usedSeconds = used.clamp(0, _limitForTier(tier)).toInt();
        _loading = false;
      });
    } catch (_) {
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
    final words = message.trim().split(RegExp(r'\s+')).where((w) => w.isNotEmpty).length;
    if (words < 5) {
      return 'Guided practice (offline): Good start. Say the same idea again with one reason or example.';
    }
    if (message.trim().endsWith('?')) {
      return 'Guided practice (offline): Nice question. Now answer it yourself in two complete English sentences.';
    }
    return 'Guided practice (offline): Well done. Add one more detail, then try saying the full answer naturally.';
  }

  int _limitForTier(String tier) => switch (tier) {
        'annual' => 86400,
        'monthly' => 21600,
        _ => 3600,
      };

  bool _isFreeTalk(Map<String, dynamic> s) {
    final title = (s['title'] ?? '').toString().toLowerCase();
    final track = (s['track'] ?? '').toString().toLowerCase();
    return title.contains('free') || track == 'free_talk';
  }

  Map<String, dynamic>? get _freeTalkScenario {
    for (final scenario in _scenarios) {
      if (_isFreeTalk(scenario)) return scenario;
    }
    return _scenarios.isEmpty ? null : _scenarios.first;
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

  String _timeLabel(int seconds) {
    final h = seconds ~/ 3600;
    final m = (seconds % 3600) ~/ 60;
    if (h > 0) return '${h}h ${m}m';
    return '${m}m';
  }

  String _voiceTime() {
    final m = (_voiceElapsed ~/ 60).toString().padLeft(2, '0');
    final s = (_voiceElapsed % 60).toString().padLeft(2, '0');
    return '$m:$s';
  }

  Future<void> _start(Map<String, dynamic> scenario, {bool voice = false}) async {
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
      _voiceMode = voice;
      _voicePaused = false;
      _voiceElapsed = 0;
    });
    try {
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
      if (voice) {
        _startVoiceTimer();
        Future<void>.delayed(const Duration(milliseconds: 300), () async {
          if (mounted && _voiceMode && !_voicePaused && !_sending && !_listening) {
            await _toggleMic();
          }
        });
      }
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _error = 'Could not start Maya conversation.';
        _sending = false;
        _voiceMode = false;
      });
    }
  }

  Future<void> _startFreeTalk({required bool voice}) async {
    final scenario = _freeTalkScenario;
    if (scenario == null) {
      setState(() => _error = 'Free Talk is unavailable right now.');
      return;
    }
    await _start(scenario, voice: voice);
  }

  void _startVoiceTimer() {
    _voiceTimer?.cancel();
    _voiceTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (!mounted || !_voiceMode || _voicePaused) return;
      setState(() => _voiceElapsed++);
    });
  }

  void _openVoiceMode() {
    _speech.stop();
    setState(() {
      _voiceMode = true;
      _voicePaused = false;
      _voiceElapsed = 0;
      _listening = false;
      _liveWords = '';
    });
    _startVoiceTimer();
    Future<void>.delayed(const Duration(milliseconds: 300), () async {
      if (mounted && _voiceMode && !_voicePaused && !_sending && !_listening) {
        await _toggleMic();
      }
    });
  }

  void _leaveVoiceMode() {
    _voiceTimer?.cancel();
    _speech.stop();
    setState(() {
      _voiceMode = false;
      _voicePaused = false;
      _listening = false;
      _liveWords = '';
    });
  }

  Future<void> _togglePause() async {
    if (!_voiceMode) return;
    if (!_voicePaused) {
      await _speech.stop();
      await _tts.stop();
    }
    setState(() {
      _voicePaused = !_voicePaused;
      _listening = false;
    });
  }

  Future<void> _toggleMic() async {
    if (_sending || _sessionId == null || _voicePaused) return;
    if (_listening) {
      await _speech.stop();
      if (mounted) setState(() => _listening = false);
      final text = _liveWords.trim();
      if (text.isNotEmpty) await _send(text);
      return;
    }
    await _tts.stop();
    final ok = await _speech.initialize();
    if (!ok) {
      if (mounted) setState(() => _error = 'Microphone speech recognition is unavailable.');
      return;
    }
    setState(() {
      _listening = true;
      _liveWords = '';
      _error = null;
    });
    await _speech.listen(
      onResult: _onSpeech,
      listenFor: const Duration(minutes: 2),
      pauseFor: const Duration(seconds: 2),
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

  Future<void> _sendText() async {
    final value = _text.text.trim();
    if (value.isEmpty) return;
    _text.clear();
    await _send(value);
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
        _tier = (data['tier'] ?? _tier).toString();
        _dailyLimitSeconds = int.tryParse((data['daily_limit_seconds'] ?? _dailyLimitSeconds).toString()) ?? _dailyLimitSeconds;
        _usedSeconds = int.tryParse((data['used_seconds'] ?? _usedSeconds).toString()) ?? _usedSeconds;
        _sending = false;
      });
      _scrollDown();
      await _recordMayaActivity();
      await _recordMayaCorrection(clean, data);
      if (reply.isNotEmpty && _speakerOn) {
        await _speak(reply, (data['tts_locale'] ?? 'en-IN').toString(), _expression);
        if (_voiceMode && !_voicePaused && mounted) {
          await Future<void>.delayed(const Duration(milliseconds: 220));
          if (_voiceMode && !_voicePaused && !_sending && !_listening && mounted) {
            await _toggleMic();
          }
        }
      }
    } catch (e) {
      if (!mounted) return;
      final raw = e.toString().toLowerCase();
      setState(() {
        _error = raw.contains('limit') || raw.contains('daily_ai_limit_reached')
            ? 'Your AI Conversation time for today is complete. It resets daily.'
            : 'Maya could not reply right now. Please try again.';
        _sending = false;
      });
    }
  }

  Future<void> _recordMayaActivity() async {
    try {
      await _client.rpc('record_my_learning_activity', params: {
        'p_minutes': 1,
        'p_xp': 3,
        'p_source': 'maya_conversation',
      });
    } catch (_) {}
  }

  Future<void> _recordMayaCorrection(String original, Map<String, dynamic> data) async {
    final correction = _nullableText(data['correction']);
    final suggested = _nullableText(data['suggested_english']);
    final improved = correction ?? suggested;
    if (improved == null || original.trim().isEmpty) return;
    try {
      final normalized = improved
          .toLowerCase()
          .replaceAll(RegExp(r'[^a-z0-9 ]'), ' ')
          .replaceAll(RegExp(r'\s+'), ' ')
          .trim();
      final key = normalized.length > 90 ? normalized.substring(0, 90) : normalized;
      if (key.length < 2) return;
      await _client.rpc('record_my_learning_mistake', params: {
        'p_category': correction != null ? 'grammar' : 'phrasing',
        'p_mistake_key': 'maya:$key',
        'p_example': original,
        'p_correction': improved,
        'p_source': 'maya_conversation',
      });
    } catch (_) {}
  }

  String? _nullableText(dynamic value) {
    final text = value?.toString().trim() ?? '';
    return text.isEmpty ? null : text;
  }

  String _safeExpression(dynamic value) {
    const allowed = {
      'calm', 'happy', 'cool', 'encouraging',
      'empathetic', 'thoughtful', 'playful', 'focused'
    };
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
    _voiceTimer?.cancel();
    await _speech.stop();
    await _tts.stop();
    if (_sessionId == null || _sessionId!.startsWith('local-')) {
      _closeConversation();
      return;
    }
    setState(() => _sending = true);
    try {
      final response = await _client.functions.invoke('ai-practice-chat', body: {
        'action': 'summarize',
        'session_id': _sessionId,
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
    _voiceTimer?.cancel();
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
      _voiceMode = false;
      _voicePaused = false;
      _voiceElapsed = 0;
      _listening = false;
      _liveWords = '';
    });
    _load();
  }

  void _scrollDown() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(
          _scroll.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    if (_active != null && _voiceMode) return _voiceView();
    if (_active != null) return _conversationView();
    return _homeView();
  }

  Widget _homeView() {
    return Scaffold(
      appBar: AppBar(
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('AI Conversation'),
            Text('Talk with Maya', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w400)),
          ],
        ),
        actions: [IconButton(onPressed: _load, icon: const Icon(Icons.help_outline_rounded))],
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _hero(),
            const SizedBox(height: 18),
            if (_error != null) ...[_errorBox(), const SizedBox(height: 12)],
            Text('Start a Conversation', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900, color: Theme.of(context).colorScheme.onSurface)),
            const SizedBox(height: 10),
            _freeTalkCard(),
            const SizedBox(height: 10),
            ..._scenarios.where((s) => !_isFreeTalk(s)).take(8).map(_scenarioCard),
            const SizedBox(height: 8),
            _dailyTimeCard(),
            const SizedBox(height: 12),
            _benefitsStrip(),
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
        gradient: LinearGradient(
          colors: [colors.primary.withValues(alpha: .96), const Color(0xFF8F64FF)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(crossAxisAlignment: CrossAxisAlignment.center, children: [
          _MayaAvatar(size: 92, expression: 'happy'),
          const SizedBox(width: 14),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Hi, I’m', style: TextStyle(color: Colors.white70, fontSize: 16)),
            const Text('Maya 👋', style: TextStyle(color: Colors.white, fontSize: 29, fontWeight: FontWeight.w900)),
            const SizedBox(height: 4),
            const Text('Your AI English Speaking Partner', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
          ])),
        ]),
        const SizedBox(height: 14),
        Row(children: [
          Expanded(child: _heroAction(Icons.chat_bubble_rounded, 'Natural Talk', 'Any Topic', () => _startFreeTalk(voice: false))),
          const SizedBox(width: 10),
          Expanded(child: _heroAction(Icons.graphic_eq_rounded, 'Voice Conversation', 'Talk Live', () => _startFreeTalk(voice: true))),
        ]),
      ]),
    );
  }

  Widget _heroAction(IconData icon, String title, String subtitle, VoidCallback onTap) {
    return Material(
      color: Colors.white.withValues(alpha: .94),
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: _sending ? null : onTap,
        child: Padding(
          padding: const EdgeInsets.all(11),
          child: Row(children: [
            Icon(icon, color: Theme.of(context).colorScheme.primary),
            const SizedBox(width: 8),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(title, style: const TextStyle(color: Color(0xFF17131F), fontWeight: FontWeight.w900, fontSize: 12)),
              Text(subtitle, style: const TextStyle(color: Color(0xFF5D566B), fontSize: 11, fontWeight: FontWeight.w600)),
            ])),
          ]),
        ),
      ),
    );
  }

  Widget _freeTalkCard() {
    return Card(
      elevation: 0,
      color: Theme.of(context).colorScheme.primaryContainer.withValues(alpha: .45),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(18),
        side: BorderSide(color: Theme.of(context).colorScheme.primary.withValues(alpha: .35)),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: _sending ? null : () => _startFreeTalk(voice: false),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(children: [
            CircleAvatar(
              radius: 23,
              backgroundColor: Theme.of(context).colorScheme.primary,
              child: const Icon(Icons.forum_rounded, color: Colors.white),
            ),
            const SizedBox(width: 12),
            const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Text('Free Talk with Maya', style: TextStyle(fontWeight: FontWeight.w900)),
                SizedBox(width: 6),
                DecoratedBox(
                  decoration: BoxDecoration(color: Colors.redAccent, borderRadius: BorderRadius.all(Radius.circular(99))),
                  child: Padding(padding: EdgeInsets.symmetric(horizontal: 7, vertical: 2), child: Text('NEW', style: TextStyle(color: Colors.white, fontSize: 9, fontWeight: FontWeight.w900))),
                ),
              ]),
              SizedBox(height: 3),
              Text('Talk about coding, news, finance, shopping, jokes, travel, work, hobbies and more.'),
            ])),
            const Icon(Icons.chevron_right_rounded),
          ]),
        ),
      ),
    );
  }

  Widget _scenarioCard(Map<String, dynamic> s) {
    final icon = _scenarioIcon((s['category'] ?? '').toString(), (s['title'] ?? '').toString());
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Card(
        elevation: .2,
        margin: EdgeInsets.zero,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: _sending ? null : () => _start(s),
          child: Padding(
            padding: const EdgeInsets.all(13),
            child: Row(children: [
              CircleAvatar(radius: 21, child: Icon(icon, size: 21)),
              const SizedBox(width: 12),
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text((s['title'] ?? '').toString(), style: const TextStyle(fontWeight: FontWeight.w800)),
                const SizedBox(height: 2),
                Text((s['description'] ?? '').toString(), maxLines: 2, overflow: TextOverflow.ellipsis),
              ])),
              const Icon(Icons.chevron_right_rounded),
            ]),
          ),
        ),
      ),
    );
  }

  IconData _scenarioIcon(String category, String title) {
    final value = '$category $title'.toLowerCase();
    if (value.contains('travel')) return Icons.flight_rounded;
    if (value.contains('work') || value.contains('business') || value.contains('career')) return Icons.work_rounded;
    if (value.contains('news')) return Icons.public_rounded;
    if (value.contains('tech') || value.contains('coding')) return Icons.laptop_mac_rounded;
    if (value.contains('interview')) return Icons.badge_rounded;
    if (value.contains('food')) return Icons.local_cafe_rounded;
    return Icons.chat_bubble_outline_rounded;
  }

  Widget _dailyTimeCard() {
    final progress = _dailyLimitSeconds <= 0 ? 0.0 : (_usedSeconds / _dailyLimitSeconds).clamp(0.0, 1.0).toDouble();
    final remaining = (_dailyLimitSeconds - _usedSeconds).clamp(0, _dailyLimitSeconds).toInt();
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.secondaryContainer.withValues(alpha: .42),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Column(children: [
        Row(children: [
          const Icon(Icons.workspace_premium_rounded),
          const SizedBox(width: 8),
          const Expanded(child: Text('Your Daily AI Time', style: TextStyle(fontWeight: FontWeight.w900))),
          Text(_limitLabel, style: const TextStyle(fontWeight: FontWeight.w900)),
        ]),
        const SizedBox(height: 10),
        ClipRRect(borderRadius: BorderRadius.circular(99), child: LinearProgressIndicator(value: progress, minHeight: 8)),
        const SizedBox(height: 7),
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Text('${_timeLabel(_usedSeconds)} used today'),
          Text('${_timeLabel(remaining)} left'),
        ]),
      ]),
    );
  }

  Widget _benefitsStrip() {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: const [
        _TinyBenefit(icon: Icons.graphic_eq_rounded, title: 'Real Voice Conversation'),
        _TinyBenefit(icon: Icons.translate_rounded, title: 'Hindi → English Help'),
        _TinyBenefit(icon: Icons.auto_fix_high_rounded, title: 'Instant Correction'),
        _TinyBenefit(icon: Icons.forum_rounded, title: 'Any Topic You Want'),
        _TinyBenefit(icon: Icons.favorite_rounded, title: 'Encouraging & Friendly'),
        _TinyBenefit(icon: Icons.shield_rounded, title: 'Safe & Positive'),
      ],
    );
  }

  Widget _conversationView() {
    final free = _active != null && _isFreeTalk(_active!);
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(Icons.arrow_back_rounded), onPressed: _closeConversation),
        titleSpacing: 0,
        title: Row(children: [
          _MayaAvatar(size: 38, expression: _expression),
          const SizedBox(width: 9),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Row(children: [
              Text('Maya', style: TextStyle(fontWeight: FontWeight.w900)),
              SizedBox(width: 5),
              Icon(Icons.circle, size: 8, color: Colors.green),
            ]),
            Text(free ? 'Online · Free Talk' : 'Online · ${(_active?['title'] ?? '').toString()}',
                maxLines: 1, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.labelSmall),
          ])),
        ]),
        actions: [
          IconButton(tooltip: 'Voice Conversation', onPressed: _openVoiceMode, icon: const Icon(Icons.graphic_eq_rounded)),
          TextButton(onPressed: _sending ? null : _end, child: const Text('End')),
        ],
      ),
      body: SafeArea(
        top: false,
        child: Column(children: [
          _coachBanner(),
          Expanded(child: _turns.isEmpty ? _starter(free) : _chatList()),
          if (_suggestedEnglish != null) _learningCard('You can say', _suggestedEnglish!, Icons.translate_rounded),
          if (_correction != null) _learningCard('Quick improvement', _correction!, Icons.auto_fix_high_rounded),
          if (_error != null) Padding(padding: const EdgeInsets.symmetric(horizontal: 14), child: _errorBox()),
          _composer(),
        ]),
      ),
    );
  }

  Widget _coachBanner() {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.fromLTRB(14, 8, 14, 0),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.primaryContainer.withValues(alpha: .45),
        borderRadius: BorderRadius.circular(14),
      ),
      child: const Row(children: [
        Icon(Icons.lightbulb_outline_rounded, size: 19),
        SizedBox(width: 8),
        Expanded(child: Text('Hindi/Hinglish is welcome. Maya converts your thought into natural English and encourages you to continue in English.')),
      ]),
    );
  }

  Widget _starter(bool free) {
    return Center(child: SingleChildScrollView(
      padding: const EdgeInsets.all(28),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        _MayaAvatar(size: 112, expression: 'happy'),
        const SizedBox(height: 14),
        Text('Hey! 😊', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
        const SizedBox(height: 6),
        Text(
          free
              ? 'What would you like to talk about today? Start in English, Hindi or Hinglish.'
              : 'Let’s practice “${_active?['title']}”. Speak naturally — I’ll help you make your English clearer and more confident.',
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 16),
        FilledButton.icon(onPressed: _openVoiceMode, icon: const Icon(Icons.graphic_eq_rounded), label: const Text('Start Voice Conversation')),
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
          child: Row(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (!mine) ...[_MayaAvatar(size: 30, expression: _expression), const SizedBox(width: 6)],
              Flexible(child: Container(
                constraints: const BoxConstraints(maxWidth: 320),
                margin: const EdgeInsets.only(bottom: 9),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
                decoration: BoxDecoration(
                  gradient: mine
                      ? const LinearGradient(colors: [Color(0xFF5C26F5), Color(0xFF7A20FF)])
                      : null,
                  color: mine ? null : Theme.of(context).colorScheme.surfaceContainerHighest,
                  borderRadius: BorderRadius.circular(17),
                ),
                child: Text(t.text, style: TextStyle(color: mine ? Colors.white : null, height: 1.3)),
              )),
            ],
          ),
        );
      },
    );
  }

  Widget _composer() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 7, 12, 12),
      child: Column(children: [
        Text('$_planLabel · $_limitLabel · resets daily', style: Theme.of(context).textTheme.labelSmall),
        const SizedBox(height: 7),
        if (_liveWords.isNotEmpty)
          Padding(padding: const EdgeInsets.only(bottom: 7), child: Text('“$_liveWords”', textAlign: TextAlign.center)),
        Row(children: [
          IconButton.filled(onPressed: _sending ? null : _toggleMic, icon: Icon(_listening ? Icons.stop_rounded : Icons.mic_rounded)),
          const SizedBox(width: 8),
          Expanded(child: TextField(
            controller: _text,
            textInputAction: TextInputAction.send,
            onSubmitted: (_) => _sendText(),
            decoration: InputDecoration(
              hintText: _sending ? 'Maya is thinking…' : 'Type or speak something…',
              filled: true,
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(18), borderSide: BorderSide.none),
            ),
          )),
          const SizedBox(width: 8),
          IconButton.filled(onPressed: _sending ? null : _sendText, icon: const Icon(Icons.send_rounded)),
        ]),
      ]),
    );
  }

  Widget _voiceView() {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(Icons.arrow_back_rounded), onPressed: _leaveVoiceMode),
        title: const Column(children: [
          Text('Voice Conversation', style: TextStyle(fontWeight: FontWeight.w900)),
          Text('Talk with Maya', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w400)),
        ]),
        actions: [IconButton(onPressed: _closeConversation, icon: const Icon(Icons.close_rounded))],
      ),
      body: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
              decoration: BoxDecoration(color: Colors.green.withValues(alpha: .12), borderRadius: BorderRadius.circular(99)),
              child: Row(mainAxisSize: MainAxisSize.min, children: [
                const Icon(Icons.graphic_eq_rounded, color: Colors.green, size: 18),
                const SizedBox(width: 6),
                Text(_voicePaused ? 'Voice Mode Paused' : 'Voice Mode Active', style: const TextStyle(fontWeight: FontWeight.w800, color: Colors.green)),
              ]),
            ),
            const Spacer(),
            _voiceWave(),
            const SizedBox(height: 18),
            _MayaAvatar(size: 142, expression: _expression),
            const SizedBox(height: 18),
            Text(
              _voicePaused
                  ? 'Voice conversation paused'
                  : _sending
                      ? 'Maya is thinking…'
                      : _listening
                          ? 'Maya is listening…'
                          : 'Ready to talk',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900),
            ),
            const SizedBox(height: 5),
            Text(_voicePaused ? 'Tap Resume when you are ready' : _listening ? 'Speak now' : 'Tap the microphone and speak naturally'),
            if (_liveWords.isNotEmpty) ...[
              const SizedBox(height: 13),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(color: Theme.of(context).colorScheme.primaryContainer.withValues(alpha: .38), borderRadius: BorderRadius.circular(14)),
                child: Text('“$_liveWords”', textAlign: TextAlign.center),
              ),
            ],
            const SizedBox(height: 22),
            GestureDetector(
              onTap: _voicePaused || _sending ? null : _toggleMic,
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 220),
                width: 104,
                height: 104,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: LinearGradient(colors: _listening
                      ? [const Color(0xFF9B5CFF), const Color(0xFF5B1DFF)]
                      : [Theme.of(context).colorScheme.primary, const Color(0xFF7B2DFF)]),
                  boxShadow: [BoxShadow(color: Theme.of(context).colorScheme.primary.withValues(alpha: .35), blurRadius: _listening ? 34 : 20, spreadRadius: _listening ? 8 : 3)],
                ),
                child: Icon(_listening ? Icons.stop_rounded : Icons.mic_rounded, color: Colors.white, size: 48),
              ),
            ),
            const SizedBox(height: 12),
            Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              const Icon(Icons.circle, size: 8, color: Colors.green),
              const SizedBox(width: 6),
              Text(_voiceTime(), style: const TextStyle(fontWeight: FontWeight.w800)),
            ]),
            const Spacer(),
            Row(children: [
              Expanded(child: OutlinedButton.icon(
                onPressed: _end,
                icon: const Icon(Icons.call_end_rounded, color: Colors.red),
                label: const Text('End'),
              )),
              const SizedBox(width: 10),
              Expanded(child: OutlinedButton.icon(
                onPressed: _togglePause,
                icon: Icon(_voicePaused ? Icons.play_arrow_rounded : Icons.pause_rounded),
                label: Text(_voicePaused ? 'Resume' : 'Pause'),
              )),
              const SizedBox(width: 10),
              Expanded(child: OutlinedButton.icon(
                onPressed: () async {
                  await _tts.stop();
                  setState(() => _speakerOn = !_speakerOn);
                },
                icon: Icon(_speakerOn ? Icons.volume_up_rounded : Icons.volume_off_rounded),
                label: const Text('Speaker'),
              )),
            ]),
            const SizedBox(height: 13),
            const Row(children: [
              Expanded(child: _VoiceBenefit(icon: Icons.forum_rounded, title: 'Natural Conversation')),
              SizedBox(width: 7),
              Expanded(child: _VoiceBenefit(icon: Icons.verified_rounded, title: 'Real-time Correction')),
              SizedBox(width: 7),
              Expanded(child: _VoiceBenefit(icon: Icons.favorite_rounded, title: 'Encouraging')),
            ]),
            const SizedBox(height: 10),
            TextButton.icon(onPressed: _leaveVoiceMode, icon: const Icon(Icons.chat_bubble_outline_rounded), label: const Text('Switch to Text Conversation')),
          ]),
        ),
      ),
    );
  }

  Widget _voiceWave() {
    final active = _listening || _sending;
    final heights = active ? [18.0, 32.0, 22.0, 44.0, 28.0, 38.0, 20.0] : [12.0, 18.0, 14.0, 22.0, 14.0, 18.0, 12.0];
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: heights.map((h) => AnimatedContainer(
        duration: const Duration(milliseconds: 260),
        margin: const EdgeInsets.symmetric(horizontal: 3),
        width: 5,
        height: h,
        decoration: BoxDecoration(color: Theme.of(context).colorScheme.primary, borderRadius: BorderRadius.circular(99)),
      )).toList(),
    );
  }

  Widget _learningCard(String title, String text, IconData icon) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.fromLTRB(14, 0, 14, 8),
      padding: const EdgeInsets.all(11),
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: [const Color(0xFFD9FFF0), Theme.of(context).colorScheme.secondaryContainer.withValues(alpha: .62)]),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(icon, size: 20),
        const SizedBox(width: 9),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.w900)),
          const SizedBox(height: 2),
          Text(text, style: const TextStyle(fontWeight: FontWeight.w600)),
        ])),
        IconButton(onPressed: () async {
          await _tts.setLanguage('en-IN');
          await _tts.speak(text);
        }, icon: const Icon(Icons.volume_up_rounded)),
      ]),
    );
  }

  Widget _errorBox() => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(10),
    decoration: BoxDecoration(
      color: Theme.of(context).colorScheme.errorContainer,
      borderRadius: BorderRadius.circular(12),
    ),
    child: Text(_error ?? '', textAlign: TextAlign.center),
  );
}

class _TinyBenefit extends StatelessWidget {
  const _TinyBenefit({required this.icon, required this.title});
  final IconData icon;
  final String title;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: .55),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 18, color: Theme.of(context).colorScheme.primary),
        const SizedBox(width: 6),
        Text(title, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w800)),
      ]),
    );
  }
}

class _VoiceBenefit extends StatelessWidget {
  const _VoiceBenefit({required this.icon, required this.title});
  final IconData icon;
  final String title;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 9),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.primaryContainer.withValues(alpha: .36),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(children: [
        Icon(icon, size: 19, color: Theme.of(context).colorScheme.primary),
        const SizedBox(height: 4),
        Text(title, textAlign: TextAlign.center, style: const TextStyle(fontSize: 9.5, fontWeight: FontWeight.w800)),
      ]),
    );
  }
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
            border: Border.all(color: primary.withValues(alpha: .78), width: 2.6),
            boxShadow: [BoxShadow(color: primary.withValues(alpha: .26), blurRadius: 18)],
          ),
          child: ClipOval(
            child: Image.asset(
              'assets/images/maya_tutor.jpg',
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => ColoredBox(
                color: Theme.of(context).colorScheme.primaryContainer,
                child: Icon(Icons.support_agent_rounded, size: size * .46),
              ),
            ),
          ),
        ),
        Positioned(
          right: 0,
          bottom: 0,
          child: Container(
            padding: const EdgeInsets.all(3),
            decoration: BoxDecoration(color: Theme.of(context).colorScheme.surface, shape: BoxShape.circle),
            child: Text(_emoji, style: TextStyle(fontSize: size * .22)),
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
      child: SingleChildScrollView(child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text('Conversation complete 🎉', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
          const SizedBox(height: 8),
          Text('English accuracy · $score%', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          Text(notes),
          if (corrections.isNotEmpty) ...[
            const SizedBox(height: 14),
            const Text('Useful corrections', style: TextStyle(fontWeight: FontWeight.w900)),
            const SizedBox(height: 6),
            ...corrections.take(3).map((c) {
              final m = c is Map ? Map<String, dynamic>.from(c) : <String, dynamic>{};
              return Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Text('• ${(m['corrected'] ?? '').toString()}'),
              );
            }),
          ],
          const SizedBox(height: 16),
          FilledButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Done')),
        ],
      )),
    );
  }
}
