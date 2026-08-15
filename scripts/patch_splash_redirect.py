from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')

# The source is stored as a ZIP in the repository and extracted during CI.
# Fresh installs were getting stuck on the Flutter splash screen because the
# unauthenticated redirect treated the splash route as a public route and
# returned null instead of moving to the login screen.

candidates = [
    root / 'lib/app/router/app_router.dart',
    root / 'lib/app/app_router.dart',
]

for path in (root / 'lib').rglob('app_router.dart'):
    if path not in candidates:
        candidates.append(path)

pattern = re.compile(
    r"if\s*\(\s*authStatus\s*==\s*AuthStatus\.unauthenticated\s*\)\s*\{\s*"
    r"return\s+isPublicPath\s*\?\s*null\s*:\s*RoutePaths\.login;\s*\}",
    re.MULTILINE,
)

replacement = """if (authStatus == AuthStatus.unauthenticated) {
      if (currentPath == RoutePaths.splash) {
        return RoutePaths.login;
      }

      return isPublicPath ? null : RoutePaths.login;
    }"""

patched = []
for path in candidates:
    if not path.exists():
        continue
    code = path.read_text()
    if 'currentPath == RoutePaths.splash' in code:
        print(f'Splash redirect fix already present: {path}')
        patched.append(path)
        continue
    new_code, count = pattern.subn(replacement, code, count=1)
    if count:
        path.write_text(new_code)
        patched.append(path)
        print(f'Patched unauthenticated splash redirect: {path}')

if not patched:
    raise SystemExit(
        'Could not apply splash redirect fix: expected unauthenticated router block not found.'
    )

# Hard verification so CI fails instead of silently producing another stuck APK.
verified = False
for path in patched:
    code = path.read_text()
    if (
        'authStatus == AuthStatus.unauthenticated' in code
        and 'currentPath == RoutePaths.splash' in code
        and 'return RoutePaths.login;' in code
    ):
        verified = True
        break

if not verified:
    raise SystemExit('Splash redirect verification failed.')

print('FluentX splash routing fix applied successfully.')
