from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')

# -----------------------------------------------------------------------------
# 1) Made for You daily practice screen
# -----------------------------------------------------------------------------
screen = root / 'lib/features/learn/presentation/screens/personalized_daily_practice_screen.dart'
screen.parent.mkdir(parents=True, exist_ok=True)
screen.write_text(r'''import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class PersonalizedDailyPracticeScreen extends StatefulWidget {
  const PersonalizedDailyPracticeScreen({super.key});

  @override
  State<PersonalizedDailyPracticeScreen> createState() => _PersonalizedDailyPracticeScreenState();
}

class _PersonalizedDailyPracticeScreenState extends State<PersonalizedDailyPracticeScreen> {
  Map<String, dynamic>? _practice;
  bool _loading = true;
  final Set<int> _doneThisSession = <int>{};

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final raw = await Supabase.instance.client.rpc('get_my_daily_personalized_practice');
      if (!mounted) return;
      setState(() {
        _practice = raw is Map ? Map<String, dynamic>.from(raw) : <String, dynamic>{};
        _loading = false;
      });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _complete(int index, Map<String, dynamic> item) async {
    if (_doneThisSession.contains(index)) return;
    try {
      final raw = await Supabase.instance.client.rpc('complete_my_daily_personalized_item', params: {
        'p_item_id': (item['id'] ?? 'item_$index').toString(),
      });
      if (!mounted) return;
      final result = raw is Map ? Map<String, dynamic>.from(raw) : <String, dynamic>{};
      setState(() {
        _doneThisSession.add(index);
        _practice?['completed_items'] = result['completed_items'] ?? ((_practice?['completed_items'] ?? 0) as num).toInt() + 1;
      });
      if (result['all_complete'] == true) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Today’s Made for You practice is complete 🎉')));
      }
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Could not save progress. Try again.')));
    }
  }

  IconData _icon(String type) {
    switch (type) {
      case 'pronunciation': return Icons.record_voice_over_rounded;
      case 'grammar': return Icons.rule_rounded;
      case 'vocabulary': return Icons.menu_book_rounded;
      case 'interview': return Icons.work_outline_rounded;
      case 'phrasing': return Icons.auto_awesome_rounded;
      default: return Icons.chat_bubble_outline_rounded;
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    if (_loading) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    if (_practice == null) {
      return Scaffold(appBar: AppBar(title: const Text('Made for You')), body: Center(child: FilledButton(onPressed: _load, child: const Text('Try again'))));
    }

    final itemsRaw = _practice!['items'];
    final items = itemsRaw is List ? itemsRaw.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList() : <Map<String, dynamic>>[];
    final completed = int.tryParse((_practice!['completed_items'] ?? 0).toString()) ?? 0;
    final total = items.length;
    final progress = total == 0 ? 0.0 : (completed / total).clamp(0.0, 1.0);

    return Scaffold(
      appBar: AppBar(title: const Text('Made for You')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              gradient: LinearGradient(colors: [colors.primaryContainer, colors.secondaryContainer]),
              borderRadius: BorderRadius.circular(22),
            ),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Row(children: [Icon(Icons.auto_awesome_rounded), SizedBox(width: 8), Text('Today’s personalized practice', style: TextStyle(fontWeight: FontWeight.w900))]),
              const SizedBox(height: 10),
              Text((_practice!['focus_title'] ?? 'Daily Confidence Boost').toString(), style: const TextStyle(fontSize: 23, fontWeight: FontWeight.w900)),
              const SizedBox(height: 6),
              Text((_practice!['focus_summary'] ?? '').toString()),
              const SizedBox(height: 14),
              LinearProgressIndicator(value: progress, minHeight: 9, borderRadius: BorderRadius.circular(99)),
              const SizedBox(height: 7),
              Text('$completed of $total completed', style: const TextStyle(fontWeight: FontWeight.w700)),
            ]),
          ),
          const SizedBox(height: 18),
          for (var i = 0; i < items.length; i++) ...[
            Builder(builder: (context) {
              final item = items[i];
              final sessionDone = _doneThisSession.contains(i);
              final answer = item['answer']?.toString();
              return Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Row(children: [
                      CircleAvatar(child: Icon(_icon((item['type'] ?? '').toString()))),
                      const SizedBox(width: 10),
                      Expanded(child: Text((item['title'] ?? 'Practice').toString(), style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16))),
                    ]),
                    const SizedBox(height: 12),
                    Text((item['prompt'] ?? '').toString(), style: const TextStyle(fontSize: 16, height: 1.4)),
                    if (answer != null && answer.trim().isNotEmpty) ...[
                      const SizedBox(height: 10),
                      ExpansionTile(
                        tilePadding: EdgeInsets.zero,
                        childrenPadding: EdgeInsets.zero,
                        title: const Text('Show better answer', style: TextStyle(fontWeight: FontWeight.w700)),
                        children: [Align(alignment: Alignment.centerLeft, child: Text(answer))],
                      ),
                    ],
                    const SizedBox(height: 8),
                    Text((item['reason'] ?? 'Personalized for you').toString(), style: TextStyle(color: colors.onSurfaceVariant, fontSize: 12)),
                    const SizedBox(height: 12),
                    FilledButton.icon(
                      onPressed: sessionDone ? null : () => _complete(i, item),
                      icon: Icon(sessionDone ? Icons.check_rounded : Icons.done_rounded),
                      label: Text(sessionDone ? 'Completed' : 'Mark complete · +5 XP'),
                    ),
                  ]),
                ),
              );
            }),
          ],
        ],
      ),
    );
  }
}
''', encoding='utf-8')

# -----------------------------------------------------------------------------
# 2) Route + Learn hub entry
# -----------------------------------------------------------------------------
routes = root / 'lib/routes/route_paths.dart'
text = routes.read_text(encoding='utf-8')
if "static const String personalizedDailyPractice" not in text:
    text = text.replace("  static const String pronunciation = '/pronunciation';", "  static const String pronunciation = '/pronunciation';\n  static const String personalizedDailyPractice = '/made-for-you';", 1)
routes.write_text(text, encoding='utf-8')

router = root / 'lib/routes/app_router.dart'
text = router.read_text(encoding='utf-8')
if 'personalized_daily_practice_screen.dart' not in text:
    text = text.replace("import '../features/learn/presentation/screens/pronunciation_practice_screen.dart';", "import '../features/learn/presentation/screens/pronunciation_practice_screen.dart';\nimport '../features/learn/presentation/screens/personalized_daily_practice_screen.dart';", 1)
if 'path: RoutePaths.personalizedDailyPractice' not in text:
    marker = "      GoRoute(\n        parentNavigatorKey: _rootNavigatorKey,\n        path: RoutePaths.pronunciation,"
    pos = text.find(marker)
    if pos < 0: raise SystemExit('Pronunciation route marker not found')
    block = """      GoRoute(\n        parentNavigatorKey: _rootNavigatorKey,\n        path: RoutePaths.personalizedDailyPractice,\n        pageBuilder: (context, state) => buildPageWithTransition(\n          context: context,\n          state: state,\n          child: const PersonalizedDailyPracticeScreen(),\n        ),\n      ),\n"""
    text = text[:pos] + block + text[pos:]
router.write_text(text, encoding='utf-8')

learn = root / 'lib/features/learn/presentation/screens/learn_hub_screen.dart'
text = learn.read_text(encoding='utf-8')
if "title: 'Made for You'" not in text:
    marker = "    _LearnModule(\n      title: 'Pronunciation',"
    pos = text.find(marker)
    if pos < 0: raise SystemExit('Pronunciation module marker not found')
    module = """    _LearnModule(\n      title: 'Made for You',\n      subtitle: 'Daily practice from your real mistakes',\n      icon: Icons.auto_awesome_rounded,\n      color: Color(0xFF7C3AED),\n      route: RoutePaths.personalizedDailyPractice,\n    ),\n"""
    text = text[:pos] + module + text[pos:]
learn.write_text(text, encoding='utf-8')

# -----------------------------------------------------------------------------
# 3) Upgrade Pronunciation Beta: weak-word targeting, history/trend, persist attempts
# -----------------------------------------------------------------------------
pron = root / 'lib/features/learn/presentation/screens/pronunciation_practice_screen.dart'
text = pron.read_text(encoding='utf-8')
if "List<String> _weakWords" not in text:
    text = text.replace("  String _feedback = 'Listen first, then repeat the sentence naturally.';", "  String _feedback = 'Listen first, then repeat the sentence naturally.';\n  List<String> _weakWords = const [];\n  List<Map<String, dynamic>> _recentAttempts = const [];", 1)

if 'void initState()' not in text:
    marker = "  @override\n  void dispose()"
    insert = r'''  @override
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

'''
    text = text.replace(marker, insert + marker, 1)

if 'List<String> _findWeakWords' not in text:
    marker = "  int _clarityScore(String expected, String recognized, double confidence) {"
    helper = r'''  List<String> _findWeakWords(String expected, String recognized) {
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

'''
    text = text.replace(marker, helper + marker, 1)

old = "      final score = _clarityScore(_target, result.recognizedWords, result.confidence);\n      setState(() {"
if old in text:
    text = text.replace(old, "      final score = _clarityScore(_target, result.recognizedWords, result.confidence);\n      final weakWords = _findWeakWords(_target, result.recognizedWords);\n      setState(() {\n        _weakWords = weakWords;", 1)

text = text.replace("      _recordActivity();", "      _recordPronunciationAttempt(score, result.recognizedWords, result.confidence, weakWords);", 1)

start = text.find("  Future<void> _recordActivity() async {")
if start >= 0:
    end = text.find("\n  void _useCustom()", start)
    replacement = r'''  Future<void> _recordPronunciationAttempt(int score, String recognized, double confidence, List<String> weakWords) async {
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
'''
    text = text[:start] + replacement + text[end:]

# reset weak words on new attempt/custom sentence
text = text.replace("      _score = null;\n      _feedback = 'Speak the sentence naturally.';", "      _score = null;\n      _weakWords = const [];\n      _feedback = 'Speak the sentence naturally.';", 1)
text = text.replace("      _score = null;\n      _feedback = 'Listen first, then repeat the sentence naturally.';", "      _score = null;\n      _weakWords = const [];\n      _feedback = 'Listen first, then repeat the sentence naturally.';", 1)

# Add weak word coaching + trend UI before end of list.
needle = "            ] else ...[\n              const SizedBox(height: 14),\n              Text(_feedback, textAlign: TextAlign.center),\n            ],\n          ],"
if needle in text and 'Words to focus on' not in text:
    extra = r'''            ] else ...[
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
          ],'''
    text = text.replace(needle, extra, 1)
pron.write_text(text, encoding='utf-8')

print('Adaptive coaching UI applied: Made for You + pronunciation weak-word intelligence + trend history.')
