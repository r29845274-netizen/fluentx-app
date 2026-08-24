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

path.write_text(text, encoding='utf-8')
print('Maya voice polish applied: faster turn-taking, barge-in, shorter silence and duplicate-listen guards.')
