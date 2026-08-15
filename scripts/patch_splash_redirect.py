from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')

# The app source is stored as a ZIP and extracted during CI. On a fresh install,
# FluentX can remain on the Flutter splash route when authentication resolves to
# unauthenticated. Force that state to leave /splash and go to /login while
# preserving the original auth-status expression used by the router.

candidates = [
    root / 'lib/routes/app_router.dart',
    root / 'lib/app/router/app_router.dart',
    root / 'lib/app/app_router.dart',
]
for path in (root / 'lib').rglob('app_router.dart'):
    if path not in candidates:
        candidates.append(path)


def find_matching_brace(text: str, opening: int) -> int:
    depth = 0
    in_single = False
    in_double = False
    escaped = False
    for i in range(opening, len(text)):
        ch = text[i]
        if escaped:
            escaped = False
            continue
        if ch == '\\' and (in_single or in_double):
            escaped = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            continue
        if in_single or in_double:
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return i
    return -1


patched_path = None
for path in candidates:
    if not path.exists():
        continue

    code = path.read_text()
    marker = 'AuthStatus.unauthenticated'
    marker_index = code.find(marker)
    if marker_index < 0:
        continue

    # Find the if-statement containing AuthStatus.unauthenticated.
    if_start = code.rfind('if', max(0, marker_index - 400), marker_index)
    open_brace = code.find('{', marker_index, marker_index + 400)
    if if_start < 0 or open_brace < 0:
        continue

    close_brace = find_matching_brace(code, open_brace)
    if close_brace < 0:
        continue

    line_start = code.rfind('\n', 0, if_start) + 1
    indent = code[line_start:if_start]
    if indent.strip():
        indent = ''

    header = code[if_start:open_brace + 1]
    replacement = (
        header
        + '\n'
        + indent
        + '  if (currentPath == RoutePaths.splash) {\n'
        + indent
        + '    return RoutePaths.login;\n'
        + indent
        + '  }\n\n'
        + indent
        + '  return isPublicPath ? null : RoutePaths.login;\n'
        + indent
        + '}'
    )

    old_block = code[if_start:close_brace + 1]
    new_code = code[:if_start] + replacement + code[close_brace + 1:]
    path.write_text(new_code)

    # Verify the exact replaced block, rather than matching unrelated splash code.
    verify_block = replacement
    required = [
        'AuthStatus.unauthenticated',
        'if (currentPath == RoutePaths.splash)',
        'return RoutePaths.login;',
        'return isPublicPath ? null : RoutePaths.login;',
    ]
    missing = [item for item in required if item not in verify_block]
    if missing:
        raise SystemExit('Splash redirect verification failed: ' + ', '.join(missing))

    print(f'Patched splash routing in: {path}')
    print('Previous unauthenticated router block:')
    print(old_block)
    print('New unauthenticated router block:')
    print(replacement)
    patched_path = path
    break

if patched_path is None:
    raise SystemExit(
        'Could not find the router block containing AuthStatus.unauthenticated.'
    )

print('FluentX splash routing fix applied successfully.')
