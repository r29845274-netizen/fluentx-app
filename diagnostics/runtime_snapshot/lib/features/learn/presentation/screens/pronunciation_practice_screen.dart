import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_recognition_result.dart';
import 'package:speech_to_text/speech_to_text.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class PronunciationPracticeScreen extends StatefulWidget {
  const PronunciationPracticeScreen({super.key});

  @override
  State<PronunciationPracticeScreen> createState() => _PronunciationPracticeScreenState();
}

class _PronunciationPracticeScreenState extends State<PronunciationPracticeScreen> {
  final _speech = SpeechToText();
  final _tts = FlutterTts();
  final _custom = TextEditingController();

  static const _phrases = <String>[
    'I would like to improve my spoken English.',
    'Could you please explain that one more time?',
    'I am confident that I can handle this responsibility.',
    'Technology is changing the way we work and learn.',
    'I would be happy to discuss this in more detail.',
    'My goal is to speak English clearly and naturally.',
  ];

  String _target = _phrases.first;
  String _heard = '';
  double _confidence = 0;
  int? _score;
  bool _listening = false;
  String _feedback = 'Listen first, then repeat the sentence naturally.';
  List<String> _weakWords = const [];
  List<Map<String, dynamic>> _recentAttempts = const [];

  @override
  void initState() {
    super.initState();
    _loadRecentAttempts();
  }

  Future<void> _loadRecentAttempts() async {
    try {
      final rows = await Supabase.instance.client
          .from('pronunciation_attempts')
          .select('clarity_score,weak_words,created_at')
          .order('created_at', ascending: false)
          .limit(5);
      if (!mounted) return;
      setState(() => _recentAttempts = (rows as List).whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList());
    } catch (_) {}
  }

  @override
  void dispose() {
    _speech.stop();
    _tts.stop();
    _custom.dispose();
    super.dispose();
  }

  String _normalize(String value) => value
      .toLowerCase()
      .replaceAll(RegExp(r"[^a-z0-9' ]"), ' ')
      .replaceAll(RegExp(r'\s+'), ' ')
      .trim();

  List<String> _words(String value) {
    final normalized = _normalize(value);
    return normalized.isEmpty ? const [] : normalized.split(' ');
  }

  int _editDistance(List<String> a, List<String> b) {
    if (a.isEmpty) return b.length;
    if (b.isEmpty) return a.length;
    final prev = List<int>.generate(b.length + 1, (i) => i);
    for (var i = 1; i <= a.length; i++) {
      var left = i;
      var diag = i - 1;
      for (var j = 1; j <= b.length; j++) {
        final up = prev[j];
        final cost = a[i - 1] == b[j - 1] ? 0 : 1;
        final next = math.min(math.min(left + 1, up + 1), diag + cost);
        prev[j] = next;
        diag = up;
        left = next;
      }
    }
    return prev[b.length];
  }

  List<String> _findWeakWords(String expected, String recognized) {
    final expectedWords = _words(expected);
    final heardWords = _words(recognized);
    final weak = <String>[];
    var searchFrom = 0;
    for (final word in expectedWords) {
      var found = -1;
      for (var i = searchFrom; i < heardWords.length; i++) {
        if (heardWords[i] == word) { found = i; break; }
      }
      if (found >= 0) {
        searchFrom = found + 1;
      } else if (word.length >= 3 && !weak.contains(word)) {
        weak.add(word);
      }
      if (weak.length >= 5) break;
    }
    return weak;
  }

  int _clarityScore(String expected, String recognized, double confidence) {
    final a = _words(expected);
    final b = _words(recognized);
    if (a.isEmpty || b.isEmpty) return 0;
    final distance = _editDistance(a, b);
    final transcriptMatch = (1 - distance / math.max(a.length, b.length)).clamp(0.0, 1.0);
    final safeConfidence = confidence > 0 ? confidence.clamp(0.0, 1.0) : transcriptMatch;
    return ((transcriptMatch * .78 + safeConfidence * .22) * 100).round().clamp(0, 100);
  }

  Future<void> _listenTarget() async {
    await _tts.stop();
    await _tts.setLanguage('en-IN');
    await _tts.setSpeechRate(.42);
    await _tts.setPitch(1.0);
    await _tts.speak(_target);
  }

  Future<void> _togglePractice() async {
    if (_listening) {
      await _speech.stop();
      if (mounted) setState(() => _listening = false);
      return;
    }
    final available = await _speech.initialize();
    if (!available) {
      if (mounted) {
        setState(() => _feedback = 'Speech recognition is unavailable on this device.');
      }
      return;
    }
    setState(() {
      _listening = true;
      _heard = '';
      _score = null;
      _weakWords = const [];
      _feedback = 'Speak the sentence naturally.';
    });
    await _speech.listen(
      onResult: _onResult,
      listenFor: const Duration(seconds: 18),
      pauseFor: const Duration(seconds: 3),
      partialResults: true,
      cancelOnError: true,
    );
  }

  void _onResult(SpeechRecognitionResult result) {
    if (!mounted) return;
    setState(() {
      _heard = result.recognizedWords;
      _confidence = result.confidence;
    });
    if (result.finalResult) {
      final score = _clarityScore(_target, result.recognizedWords, result.confidence);
      final weakWords = _findWeakWords(_target, result.recognizedWords);
      setState(() {
        _weakWords = weakWords;
        _listening = false;
        _score = score;
        _feedback = score >= 90
            ? 'Excellent clarity. Try saying it once more with relaxed, natural rhythm.'
            : score >= 75
                ? 'Good job. Slow down slightly and make every key word clear.'
                : score >= 55
                    ? 'Nice attempt. Listen again and focus on the words that changed or disappeared.'
                    : 'Try again slowly. Break the sentence into two short parts first.';
      });
      _recordPronunciationAttempt(score, result.recognizedWords, result.confidence, weakWords);
    }
  }

  Future<void> _recordPronunciationAttempt(int score, String recognized, double confidence, List<String> weakWords) async {
    try {
      await Supabase.instance.client.rpc('record_my_pronunciation_attempt', params: {
        'p_target_text': _target,
        'p_recognized_text': recognized,
        'p_clarity_score': score,
        'p_confidence_score': confidence > 0 ? confidence : null,
        'p_weak_words': weakWords,
      });
      await _loadRecentAttempts();
    } catch (_) {}
  }

  void _useCustom() {
    final value = _custom.text.trim();
    if (value.isEmpty) return;
    setState(() {
      _target = value;
      _heard = '';
      _score = null;
      _weakWords = const [];
      _feedback = 'Listen first, then repeat the sentence naturally.';
    });
    FocusScope.of(context).unfocus();
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: const Text('Pronunciation Practice')),
      body: SafeArea(
        top: false,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: LinearGradient(colors: [colors.primaryContainer, colors.secondaryContainer]),
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  Icon(Icons.record_voice_over_rounded),
                  SizedBox(width: 8),
                  Text('Pronunciation Practice · Beta', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 18)),
                ]),
                SizedBox(height: 7),
                Text('Practice clear spoken English with listen → repeat → instant speech-clarity feedback.'),
                SizedBox(height: 6),
                Text('Note: this score uses speech recognition and transcript matching; it is not phoneme-level accent analysis.', style: TextStyle(fontSize: 11)),
              ]),
            ),
            const SizedBox(height: 18),
            Text('Practice sentence', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              value: _phrases.contains(_target) ? _target : null,
              items: _phrases.map((p) => DropdownMenuItem(value: p, child: Text(p, maxLines: 2, overflow: TextOverflow.ellipsis))).toList(),
              onChanged: (value) {
                if (value == null) return;
                setState(() {
                  _target = value;
                  _score = null;
                  _heard = '';
                });
              },
              decoration: const InputDecoration(border: OutlineInputBorder(), labelText: 'Choose a sentence'),
            ),
            const SizedBox(height: 10),
            Row(children: [
              Expanded(child: TextField(
                controller: _custom,
                maxLength: 180,
                decoration: const InputDecoration(border: OutlineInputBorder(), labelText: 'Or type your own sentence', counterText: ''),
              )),
              const SizedBox(width: 8),
              FilledButton.tonal(onPressed: _useCustom, child: const Text('Use')),
            ]),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(color: colors.surfaceContainerHighest, borderRadius: BorderRadius.circular(18)),
              child: Column(children: [
                Text(_target, textAlign: TextAlign.center, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, height: 1.35)),
                const SizedBox(height: 14),
                OutlinedButton.icon(onPressed: _listenTarget, icon: const Icon(Icons.volume_up_rounded), label: const Text('Listen to Maya')),
                const SizedBox(height: 10),
                FilledButton.icon(
                  style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(52)),
                  onPressed: _togglePractice,
                  icon: Icon(_listening ? Icons.stop_rounded : Icons.mic_rounded),
                  label: Text(_listening ? 'Stop' : 'Repeat Sentence'),
                ),
              ]),
            ),
            if (_heard.isNotEmpty) ...[
              const SizedBox(height: 14),
              Text('I heard:', style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 4),
              Text('“$_heard”', style: const TextStyle(fontWeight: FontWeight.w600)),
            ],
            if (_score != null) ...[
              const SizedBox(height: 18),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(color: colors.primaryContainer.withValues(alpha: .55), borderRadius: BorderRadius.circular(18)),
                child: Column(children: [
                  Text('Speech Clarity Score', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
                  const SizedBox(height: 8),
                  Text('${_score!}%', style: TextStyle(fontSize: 42, fontWeight: FontWeight.w900, color: colors.primary)),
                  const SizedBox(height: 4),
                  Text(_feedback, textAlign: TextAlign.center),
                  const SizedBox(height: 12),
                  LinearProgressIndicator(value: _score! / 100, minHeight: 9, borderRadius: BorderRadius.circular(99)),
                ]),
              ),
            ] else ...[
              const SizedBox(height: 14),
              Text(_feedback, textAlign: TextAlign.center),
            ],
            if (_weakWords.isNotEmpty) ...[
              const SizedBox(height: 16),
              Text('Words to focus on', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: _weakWords.map((word) => ActionChip(
                  avatar: const Icon(Icons.volume_up_rounded, size: 17),
                  label: Text(word),
                  onPressed: () async {
                    await _tts.stop();
                    await _tts.setLanguage('en-IN');
                    await _tts.setSpeechRate(.34);
                    await _tts.speak(word);
                  },
                )).toList(),
              ),
              const SizedBox(height: 7),
              const Text('These are words the speech recognizer missed or changed. Practice them individually, then repeat the full sentence.', style: TextStyle(fontSize: 12)),
            ],
            if (_recentAttempts.isNotEmpty) ...[
              const SizedBox(height: 20),
              Text('Recent clarity trend', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
              const SizedBox(height: 8),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: _recentAttempts.reversed.map((row) {
                      final value = int.tryParse((row['clarity_score'] ?? 0).toString()) ?? 0;
                      return Column(children: [
                        SizedBox(height: 58, child: Align(alignment: Alignment.bottomCenter, child: Container(width: 12, height: 8 + value * .45, decoration: BoxDecoration(color: colors.primary, borderRadius: BorderRadius.circular(99))))),
                        const SizedBox(height: 5),
                        Text('$value', style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 11)),
                      ]);
                    }).toList(),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
