from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
path = root / 'lib/features/ai_practice/presentation/screens/ai_practice_hub_screen.dart'
if not path.exists():
    raise SystemExit(f'Maya screen not found: {path}')

text = path.read_text(encoding='utf-8')

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
    if needle not in text:
        raise SystemExit('Maya reply completion marker not found')
    text = text.replace(
        needle,
        "      _scrollDown();\n      await _recordMayaCorrection(clean, data);\n      if (reply.isNotEmpty && _speakerOn) {",
        1,
    )

path.write_text(text, encoding='utf-8')
print('Maya corrections now feed the authenticated learner mistake profile.')
