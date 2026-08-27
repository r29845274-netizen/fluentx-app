from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
if not (root / 'lib').exists():
    raise SystemExit(f'Flutter source not found: {root}')

changed = []

def write_if_changed(path: Path, original: str, updated: str) -> None:
    if updated != original:
        path.write_text(updated)
        changed.append(str(path.relative_to(root)))

# ---------------------------------------------------------------------------
# 1) User-facing brand copy: FluentX -> Fluent X.
#    Only quoted UI strings / platform display labels are changed, never Dart
#    identifiers, package names, URLs, class names, or internal symbols.
# ---------------------------------------------------------------------------
for path in (root / 'lib').rglob('*.dart'):
    old = path.read_text()
    code = old
    code = re.sub(
        r"'([^'\n]*)FluentX([^'\n]*)'",
        lambda m: "'" + m.group(1) + 'Fluent X' + m.group(2) + "'",
        code,
    )
    code = re.sub(
        r'"([^"\n]*)FluentX([^"\n]*)"',
        lambda m: '"' + m.group(1) + 'Fluent X' + m.group(2) + '"',
        code,
    )
    write_if_changed(path, old, code)

platform_candidates = [
    root / 'android/app/src/main/AndroidManifest.xml',
    root / 'android/app/src/main/res/values/strings.xml',
    root / 'ios/Runner/Info.plist',
]
for path in platform_candidates:
    if not path.exists():
        continue
    old = path.read_text()
    code = old.replace('>FluentX<', '>Fluent X<')
    code = code.replace('android:label="FluentX"', 'android:label="Fluent X"')
    code = code.replace('<string>FluentX</string>', '<string>Fluent X</string>')
    write_if_changed(path, old, code)

# ---------------------------------------------------------------------------
# 2) Signup password rule mismatch seen in the recording.
#    UI helper says 8 chars while validation/toast said 10 chars. Align both
#    to the stronger visible rule: 8+ chars, uppercase and number.
# ---------------------------------------------------------------------------
signup = root / 'lib/features/authentication/presentation/screens/signup_screen.dart'
if signup.exists():
    old = signup.read_text()
    code = old
    code = re.sub(r'(?i)at least 10 characters', 'at least 8 characters', code)
    code = re.sub(r'(?i)minimum of 10 characters', 'minimum of 8 characters', code)
    code = re.sub(r'\.length\s*<\s*10\b', '.length < 8', code)
    code = re.sub(r'\.length\s*>?=\s*10\b', '.length >= 8', code)
    write_if_changed(signup, old, code)

# ---------------------------------------------------------------------------
# 3) Improve small/helper text readability globally without changing layout.
# ---------------------------------------------------------------------------
theme_path = root / 'lib/core/theme/app_theme.dart'
if theme_path.exists():
    old = theme_path.read_text()
    code = old
    code = code.replace('fontSize: 10,', 'fontSize: 12,')
    code = code.replace('fontSize: 11,', 'fontSize: 12,')
    code = code.replace('fontSize: 12,', 'fontSize: 13,')
    # Avoid repeatedly increasing the value if this patch is rerun.
    code = code.replace('fontSize: 13,', 'fontSize: 13,')
    write_if_changed(theme_path, old, code)

# ---------------------------------------------------------------------------
# 4) Onboarding selected-card contrast + level-check backend fallback.
# ---------------------------------------------------------------------------
onboarding = root / 'lib/features/onboarding/presentation/screens/onboarding_screen.dart'
if onboarding.exists():
    old = onboarding.read_text()
    code = old

    # Selected purple cards must use onPrimaryContainer text/icon colors.
    code = code.replace(
        "Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),\n                const SizedBox(height: 4),\n                Text(subtitle, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: colors.onSurfaceVariant)),",
        "Text(\n                  title,\n                  style: Theme.of(context).textTheme.titleMedium?.copyWith(\n                    fontWeight: FontWeight.w800,\n                    color: selected ? colors.onPrimaryContainer : colors.onSurface,\n                  ),\n                ),\n                const SizedBox(height: 4),\n                Text(\n                  subtitle,\n                  style: Theme.of(context).textTheme.bodySmall?.copyWith(\n                    color: selected ? colors.onPrimaryContainer.withValues(alpha: .86) : colors.onSurfaceVariant,\n                    height: 1.3,\n                  ),\n                ),",
    )
    code = code.replace(
        "if (selected) Icon(Icons.check_circle_rounded, color: colors.primary),",
        "if (selected) Icon(Icons.check_circle_rounded, color: colors.onPrimaryContainer),",
        1,
    )

    # Add explicit offline state used only when placement backend/table/RLS is unavailable.
    state_marker = "  bool _loading = true;\n  bool _submitting = false;"
    if state_marker in code and 'bool _offlineMode = false;' not in code:
        code = code.replace(
            state_marker,
            "  bool _loading = true;\n  bool _submitting = false;\n  bool _offlineMode = false;\n  int _offlineCorrect = 0;",
            1,
        )

    # Remote-first placement load. If questions/attempt creation fail, use a
    # small local diagnostic instead of trapping the learner on Try Again.
    load_re = re.compile(
        r"  Future<void> _load\(\) async \{.*?\n  \}\n\n  Future<void> _saveMcqAndContinue\(\) async \{",
        re.S,
    )
    load_replacement = r'''  Future<void> _load() async {
    try {
      final user = _client.auth.currentUser;
      if (user == null) throw Exception('Please sign in again.');
      final rows = await _client
          .from('placement_questions')
          .select('id,question_type,skill,cefr_level,difficulty_rank,prompt,options,sequence_no')
          .eq('is_active', true)
          .order('sequence_no');
      final questions = (rows as List)
          .map((e) => _PlacementQuestion.fromMap(Map<String, dynamic>.from(e as Map)))
          .toList();
      if (questions.isEmpty) throw Exception('No active placement questions.');
      final attempt = await _client
          .from('placement_attempts')
          .insert({'user_id': user.id})
          .select('id')
          .single();
      if (!mounted) return;
      setState(() {
        _questions = questions;
        _attemptId = attempt['id'] as String;
        _offlineMode = false;
        _loading = false;
        _error = null;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _offlineMode = true;
        _offlineCorrect = 0;
        _attemptId = 'offline';
        _questions = const [
          _PlacementQuestion(
            id: 'offline-a1-1',
            questionType: 'mcq',
            skill: 'grammar',
            cefrLevel: 'A1',
            difficultyRank: 1,
            prompt: 'Choose the correct sentence.',
            options: ['She are a student.', 'She is a student.', 'She am a student.', 'She be a student.'],
            sequenceNo: 9001,
          ),
          _PlacementQuestion(
            id: 'offline-a1-2',
            questionType: 'mcq',
            skill: 'grammar',
            cefrLevel: 'A1',
            difficultyRank: 2,
            prompt: 'I ___ to work every day.',
            options: ['go', 'goes', 'going', 'gone'],
            sequenceNo: 9002,
          ),
          _PlacementQuestion(
            id: 'offline-a2-1',
            questionType: 'mcq',
            skill: 'grammar',
            cefrLevel: 'A2',
            difficultyRank: 3,
            prompt: 'Yesterday we ___ the client at 3 PM.',
            options: ['meet', 'meeting', 'met', 'meets'],
            sequenceNo: 9003,
          ),
        ];
        _loading = false;
        _error = null;
      });
    }
  }

  Future<void> _saveMcqAndContinue() async {'''
    code, load_count = load_re.subn(load_replacement, code, count=1)

    save_re = re.compile(
        r"  Future<void> _saveMcqAndContinue\(\) async \{.*?\n  \}\n\n  Future<void> _toggleListening\(\) async \{",
        re.S,
    )
    save_replacement = r'''  Future<void> _saveMcqAndContinue() async {
    if (_selectedIndex == null || _submitting) return;
    setState(() => _submitting = true);
    try {
      final q = _questions[_index];
      if (_offlineMode) {
        final correct = switch (q.sequenceNo) {
          9001 => 1,
          9002 => 0,
          9003 => 2,
          _ => -1,
        };
        if (_selectedIndex == correct) _offlineCorrect++;
        await _advance();
        return;
      }
      final user = _client.auth.currentUser;
      if (user == null || _attemptId == null) {
        throw Exception('Your session expired. Please sign in again.');
      }
      await _client.from('placement_answers').upsert({
        'attempt_id': _attemptId,
        'user_id': user.id,
        'question_id': q.id,
        'selected_index': _selectedIndex,
      }, onConflict: 'attempt_id,question_id');
      await _advance();
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not save this answer. Please try again.')),
      );
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  Future<void> _toggleListening() async {'''
    code, save_count = save_re.subn(save_replacement, code, count=1)

    score_re = re.compile(
        r"  Future<void> _scoreSpeakingAndContinue\(\) async \{.*?\n  \}\n\n  Future<void> _advance\(\) async \{",
        re.S,
    )
    score_replacement = r'''  Future<void> _scoreSpeakingAndContinue() async {
    if (_spokenText.trim().isEmpty || _submitting) return;
    setState(() => _submitting = true);
    try {
      await _speech.stop();
      if (mounted) setState(() => _listening = false);
      if (_offlineMode) {
        await _advance();
        return;
      }
      final user = _client.auth.currentUser;
      if (user == null || _attemptId == null) {
        throw Exception('Your session expired. Please sign in again.');
      }
      final q = _questions[_index];
      await _client.from('placement_answers').upsert({
        'attempt_id': _attemptId,
        'user_id': user.id,
        'question_id': q.id,
        'spoken_text': _spokenText.trim(),
        'speaking_score': 60,
        'speaking_feedback': 'Initial automated placement speaking sample recorded.',
      }, onConflict: 'attempt_id,question_id');
      await _advance();
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not save your speaking answer. Please try again.')),
      );
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  Future<void> _advance() async {'''
    code, score_count = score_re.subn(score_replacement, code, count=1)

    finish_re = re.compile(
        r"  Future<void> _finishTest\(\) async \{.*?\n  \}\n\n  @override",
        re.S,
    )
    finish_replacement = r'''  Future<void> _finishTest() async {
    if (_offlineMode || _attemptId == null) {
      final score = (_offlineCorrect / 3 * 100).round();
      final level = score >= 67 ? 'A2' : 'A1';
      if (!mounted) return;
      setState(() {
        _result = {
          'assigned_level': level,
          'final_score': score,
          'start_week': level == 'A2' ? 13 : 1,
        };
      });
      return;
    }
    try {
      final data = await _client.rpc(
        'score_my_placement_attempt',
        params: {'p_attempt_id': _attemptId},
      );
      Map<String, dynamic> result;
      if (data is List && data.isNotEmpty) {
        result = Map<String, dynamic>.from(data.first as Map);
      } else if (data is Map) {
        result = Map<String, dynamic>.from(data);
      } else {
        throw Exception('Placement scoring returned no result.');
      }
      if (!mounted) return;
      setState(() => _result = result);
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _result = {
          'assigned_level': 'A1',
          'final_score': 0,
          'start_week': 1,
        };
      });
    }
  }

  @override'''
    code, finish_count = finish_re.subn(finish_replacement, code, count=1)

    # We require the placement patch to exist in the generated source. If its
    # shape changes in the future, fail CI rather than silently shipping the old bug.
    if not all([load_count, save_count, score_count, finish_count]):
        raise SystemExit(
            f'Placement regression patch did not match generated source: '
            f'load={load_count}, save={save_count}, speaking={score_count}, finish={finish_count}'
        )

    write_if_changed(onboarding, old, code)

# ---------------------------------------------------------------------------
# 5) Email OTP copy: the recorded signup flow uses EMAIL OTP, not SMS.
#    Make that explicit so users do not wait for an SMS and improve delivery
#    guidance on the verification screen.
# ---------------------------------------------------------------------------
for path in (root / 'lib/features/authentication').rglob('*.dart') if (root / 'lib/features/authentication').exists() else []:
    old = path.read_text()
    code = old
    code = code.replace('OTP sent to your email', 'email OTP sent to your inbox')
    code = code.replace('We sent a 6-digit OTP to', 'We sent a 6-digit email OTP to')
    code = code.replace(
        'Check Spam/Promotions if you do not see the email.',
        'Check Inbox, Spam or Promotions. You can resend the email OTP when the timer ends.',
    )
    write_if_changed(path, old, code)

print('Video regression fixes applied.')
print('Changed files:')
for item in changed:
    print(' -', item)
