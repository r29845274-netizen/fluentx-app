from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
path = root / 'lib/features/ai_practice/presentation/screens/ai_practice_hub_screen.dart'
if not path.exists():
    raise SystemExit(f'Maya screen not found: {path}')

text = path.read_text(encoding='utf-8')
replacements = {
    "_usedSeconds = used.clamp(0, _limitForTier(tier));":
        "_usedSeconds = used.clamp(0, _limitForTier(tier)).toInt();",
    "final progress = _dailyLimitSeconds <= 0 ? 0.0 : (_usedSeconds / _dailyLimitSeconds).clamp(0.0, 1.0);":
        "final progress = _dailyLimitSeconds <= 0 ? 0.0 : (_usedSeconds / _dailyLimitSeconds).clamp(0.0, 1.0).toDouble();",
    "final remaining = (_dailyLimitSeconds - _usedSeconds).clamp(0, _dailyLimitSeconds);":
        "final remaining = (_dailyLimitSeconds - _usedSeconds).clamp(0, _dailyLimitSeconds).toInt();",
    "if (_sessionId == null) return _closeConversation();":
        "if (_sessionId == null) {\n      _closeConversation();\n      return;\n    }",
}

for old, new in replacements.items():
    if old in text:
        text = text.replace(old, new)

# Guard against regressions in the generated Maya screen.
for forbidden in [
    "_usedSeconds = used.clamp(0, _limitForTier(tier));",
    "final remaining = (_dailyLimitSeconds - _usedSeconds).clamp(0, _dailyLimitSeconds);",
    "if (_sessionId == null) return _closeConversation();",
]:
    if forbidden in text:
        raise SystemExit(f'Unfixed Maya compile pattern: {forbidden}')

path.write_text(text, encoding='utf-8')
print('Maya compile safety fixes applied.')
