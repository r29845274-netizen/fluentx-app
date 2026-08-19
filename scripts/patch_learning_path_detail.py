from pathlib import Path
import sys, zlib, base64

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
assets = Path(__file__).resolve().parent / 'payloads'

payload = assets / 'learning_path_screen.b64'
if not payload.exists():
    raise SystemExit(f'Missing payload: {payload}')

screen = zlib.decompress(base64.b64decode(payload.read_text().strip())).decode('utf-8')
screen_path = root / 'lib/features/learn/presentation/screens/learning_path_screen.dart'
screen_path.parent.mkdir(parents=True, exist_ok=True)
screen_path.write_text(screen)

route_paths = root / 'lib/routes/route_paths.dart'
routes = route_paths.read_text()
if "static const String learningPath = '/learning-path';" not in routes:
    marker = "  static const String vocabulary = '/vocabulary';\n"
    if marker not in routes:
        raise SystemExit('RoutePaths insertion marker not found')
    routes = routes.replace(marker, "  static const String learningPath = '/learning-path';\n" + marker, 1)
route_paths.write_text(routes)

router_path = root / 'lib/routes/app_router.dart'
router = router_path.read_text()
import_line = "import '../features/learn/presentation/screens/learn_hub_screen.dart';\n"
new_import = "import '../features/learn/presentation/screens/learning_path_screen.dart';\n"
if new_import not in router:
    if import_line not in router:
        raise SystemExit('Router import marker not found')
    router = router.replace(import_line, import_line + new_import, 1)

if 'path: RoutePaths.learningPath,' not in router:
    marker = "      GoRoute(\n        parentNavigatorKey: _rootNavigatorKey,\n        path: RoutePaths.vocabulary,"
    block = "      GoRoute(\n        parentNavigatorKey: _rootNavigatorKey,\n        path: RoutePaths.learningPath,\n        pageBuilder: (context, state) => buildPageWithTransition(\n          context: context,\n          state: state,\n          child: const LearningPathScreen(),\n        ),\n      ),\n"
    if marker not in router:
        raise SystemExit('Router route insertion marker not found')
    router = router.replace(marker, block + marker, 1)
router_path.write_text(router)

learn_path = root / 'lib/features/learn/presentation/screens/learn_hub_screen.dart'
learn = learn_path.read_text()
marker = "                final title = (current?['title'] ?? 'Personalized English').toString();\n                return AppCard(\n                  child: Column("
replacement = "                final title = (current?['title'] ?? 'Personalized English').toString();\n                return AppCard(\n                  onTap: () => context.push(RoutePaths.learningPath),\n                  child: Column("
if marker in learn:
    learn = learn.replace(marker, replacement, 1)
elif 'RoutePaths.learningPath' not in learn:
    raise SystemExit('Personalized path card marker not found; detailed path not wired')
learn_path.write_text(learn)

print('Detailed learning path screen + route applied successfully.')
