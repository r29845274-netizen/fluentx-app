from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')

# The source is stored as a ZIP and extracted during CI. Keep the existing
# branded Flutter splash visible for a short minimum duration, then route based
# on the resolved authentication state. This avoids both previous failure modes:
# staying forever on /splash and skipping the FluentX splash entirely.

candidates = [
    root / 'lib/routes/app_router.dart',
    root / 'lib/app/router/app_router.dart',
    root / 'lib/app/app_router.dart',
]
for path in (root / 'lib').rglob('app_router.dart'):
    if path not in candidates:
        candidates.append(path)

patched_path = None
for path in candidates:
    if not path.exists():
        continue

    code = path.read_text()
    if 'AuthStatus.unauthenticated' not in code or 'RoutePaths.splash' not in code:
        continue

    # 1) Add a single launch timestamp and minimum branded splash duration.
    root_key = 'final _rootNavigatorKey = GlobalKey<NavigatorState>();'
    timing_block = '''final _rootNavigatorKey = GlobalKey<NavigatorState>();

final _routerStartedAt = DateTime.now();
const _minimumSplashDuration = Duration(milliseconds: 1200);'''
    if '_minimumSplashDuration' not in code:
        if root_key not in code:
            raise SystemExit('Could not find root navigator key for splash timing patch.')
        code = code.replace(root_key, timing_block, 1)

    # 2) GoRouter supports FutureOr<String?> redirects, so make this callback async.
    sync_redirect = 'redirect: (context, state) {'
    async_redirect = 'redirect: (context, state) async {'
    if sync_redirect in code:
        code = code.replace(sync_redirect, async_redirect, 1)
    elif async_redirect not in code:
        raise SystemExit('Could not find GoRouter redirect callback.')

    # 3) Once auth has resolved, keep the Flutter splash visible until the
    # minimum launch duration has elapsed. This applies to signed-out,
    # onboarding, and already-authenticated users.
    unknown_block = '''      if (authStatus == AuthStatus.unknown) {
        return currentPath == RoutePaths.splash ? null : RoutePaths.splash;
      }
'''
    delay_block = '''      if (authStatus == AuthStatus.unknown) {
        return currentPath == RoutePaths.splash ? null : RoutePaths.splash;
      }

      if (currentPath == RoutePaths.splash) {
        final elapsed = DateTime.now().difference(_routerStartedAt);
        final remainingMs =
            _minimumSplashDuration.inMilliseconds - elapsed.inMilliseconds;
        if (remainingMs > 0) {
          await Future<void>.delayed(Duration(milliseconds: remainingMs));
        }
      }
'''
    if 'remainingMs =' not in code:
        if unknown_block not in code:
            raise SystemExit('Could not find unknown-auth splash block.')
        code = code.replace(unknown_block, delay_block, 1)

    # 4) Signed-out users must leave splash after the delay instead of treating
    # splash as an indefinitely valid public route.
    original_unauth = '''      if (authStatus == AuthStatus.unauthenticated) {
        // Signed out and trying to reach a protected route → login.
        return isPublicPath ? null : RoutePaths.login;
      }'''
    fixed_unauth = '''      if (authStatus == AuthStatus.unauthenticated) {
        // Fresh signed-out launch: show splash briefly, then open login.
        if (currentPath == RoutePaths.splash) {
          return RoutePaths.login;
        }

        return isPublicPath ? null : RoutePaths.login;
      }'''
    if 'Fresh signed-out launch' not in code:
        if original_unauth not in code:
            raise SystemExit('Could not find unauthenticated router block.')
        code = code.replace(original_unauth, fixed_unauth, 1)

    required = [
        'redirect: (context, state) async {',
        '_minimumSplashDuration = Duration(milliseconds: 1200)',
        'await Future<void>.delayed(Duration(milliseconds: remainingMs));',
        'if (currentPath == RoutePaths.splash)',
        'return RoutePaths.login;',
    ]
    missing = [item for item in required if item not in code]
    if missing:
        raise SystemExit('Splash patch verification failed: ' + ', '.join(missing))

    path.write_text(code)
    patched_path = path
    print(f'Patched branded splash timing and routing in: {path}')
    print('Minimum FluentX splash duration: 1200 ms')
    break

if patched_path is None:
    raise SystemExit('Could not locate FluentX app_router.dart for splash patching.')

print('FluentX splash timing + redirect fix applied successfully.')
