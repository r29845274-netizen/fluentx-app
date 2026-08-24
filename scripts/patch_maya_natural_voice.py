from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
path = root / 'lib/features/ai_practice/presentation/screens/ai_practice_hub_screen.dart'
if not path.exists():
    raise SystemExit(f'Maya screen not found: {path}')

text = path.read_text(encoding='utf-8')

# Stop Maya speech immediately when the learner wants to speak (barge-in).
needle = "    final ok = await _speech.initialize();"
if needle in text and "    await _tts.stop();\n    final ok = await _speech.initialize();" not in text:
    text = text.replace(needle, "    await _tts.stop();\n    final ok = await _speech.initialize();", 1)

# Faster end-of-utterance detection for a more conversational feel.
text = text.replace(
    "      pauseFor: const Duration(seconds: 3),",
    "      pauseFor: const Duration(seconds: 2),",
    1,
)

# Voice mode: reopen microphone shortly after Maya finishes speaking.
needle = "        await _speak(reply, (data['tts_locale'] ?? 'en-IN').toString(), _expression);\n      }"
replacement = """        await _speak(reply, (data['tts_locale'] ?? 'en-IN').toString(), _expression);
        if (_voiceMode && !_voicePaused && mounted) {
          await Future<void>.delayed(const Duration(milliseconds: 220));
          if (_voiceMode && !_voicePaused && !_sending && !_listening && mounted) {
            await _toggleMic();
          }
        }
      }"""
if needle in text and replacement not in text:
    text = text.replace(needle, replacement, 1)

# Entering voice mode should start listening quickly.
needle = "    _startVoiceTimer();\n  }\n\n  void _leaveVoiceMode()"
replacement = """    _startVoiceTimer();
    Future<void>.delayed(const Duration(milliseconds: 300), () async {
      if (mounted && _voiceMode && !_voicePaused && !_sending && !_listening) {
        await _toggleMic();
      }
    });
  }

  void _leaveVoiceMode()"""
if needle in text and replacement not in text:
    text = text.replace(needle, replacement, 1)

# Starting directly from the Voice Conversation CTA also starts listening.
needle = "      if (voice) _startVoiceTimer();"
replacement = """      if (voice) {
        _startVoiceTimer();
        Future<void>.delayed(const Duration(milliseconds: 300), () async {
          if (mounted && _voiceMode && !_voicePaused && !_sending && !_listening) {
            await _toggleMic();
          }
        });
      }"""
if needle in text and replacement not in text:
    text = text.replace(needle, replacement, 1)

# Capture useful Maya corrections using the authenticated app client so they
# become inputs for the Made for You daily practice engine.
if 'Future<void> _recordMayaCorrection(' not in text:
    marker = "  String? _nullableText(dynamic value) {"
    method = r'''  Future<void> _recordMayaCorrection(String original, Map<String, dynamic> data) async {
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

'''
    if marker not in text:
        raise SystemExit('Maya nullable-text marker not found')
    text = text.replace(marker, method + marker, 1)

needle = "      _scrollDown();\n      await _recordMayaActivity();"
if needle in text and "await _recordMayaCorrection(clean, data);" not in text:
    text = text.replace(
        needle,
        "      _scrollDown();\n      await _recordMayaActivity();\n      await _recordMayaCorrection(clean, data);",
        1,
    )
elif "await _recordMayaCorrection(clean, data);" not in text:
    needle = "      _scrollDown();\n      if (reply.isNotEmpty && _speakerOn) {"
    if needle in text:
        text = text.replace(
            needle,
            "      _scrollDown();\n      await _recordMayaCorrection(clean, data);\n      if (reply.isNotEmpty && _speakerOn) {",
            1,
        )

path.write_text(text, encoding='utf-8')
print('Maya voice polish + correction capture applied: faster turn-taking, barge-in and adaptive mistake feed.')
