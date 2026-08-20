from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding='utf-8')
    if new in text:
        print(f'{label}: already applied')
        return
    if old not in text:
        raise SystemExit(f'{label}: expected source block not found in {path}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')
    print(f'{label}: updated {path}')

# 1) Final nav order: Home / Learn / Practice / Progress / Profile,
# with filled active icons for clearer selected state.
shell = root / 'lib/shared/widgets/navigation/app_shell.dart'
old_items = """  static const _items = [
    AppNavItem(icon: Icons.home_outlined, activeIcon: Icons.home_outlined, label: 'Home'),
    AppNavItem(icon: Icons.mic_none, activeIcon: Icons.mic_none, label: 'Practice'),
    AppNavItem(icon: Icons.menu_book_outlined, activeIcon: Icons.menu_book_outlined, label: 'Learn'),
    AppNavItem(
      icon: Icons.bar_chart,
      activeIcon: Icons.bar_chart,
      label: 'Progress',
    ),
    AppNavItem(icon: Icons.person_outline, activeIcon: Icons.person_outline, label: 'Profile'),
  ];
"""
new_items = """  static const _items = [
    AppNavItem(icon: Icons.home_outlined, activeIcon: Icons.home, label: 'Home'),
    AppNavItem(icon: Icons.menu_book_outlined, activeIcon: Icons.menu_book, label: 'Learn'),
    AppNavItem(icon: Icons.mic_none, activeIcon: Icons.mic, label: 'Practice'),
    AppNavItem(
      icon: Icons.bar_chart_outlined,
      activeIcon: Icons.bar_chart,
      label: 'Progress',
    ),
    AppNavItem(icon: Icons.person_outline, activeIcon: Icons.person, label: 'Profile'),
  ];
"""
replace_once(shell, old_items, new_items, 'bottom-nav visual order')

# 2) Keep GoRouter branch indexes aligned with the visual tab order.
router = root / 'lib/routes/app_router.dart'
router_text = router.read_text(encoding='utf-8')
ai_branch = """          StatefulShellBranch(
            routes: [
              GoRoute(
                path: RoutePaths.aiPractice,
                pageBuilder: (context, state) => buildPageWithTransition(
                  context: context,
                  state: state,
                  child: const AiPracticeHubScreen(),
                ),
              ),
            ],
          ),
"""
learn_branch = """          StatefulShellBranch(
            routes: [
              GoRoute(
                path: RoutePaths.learn,
                pageBuilder: (context, state) => buildPageWithTransition(
                  context: context,
                  state: state,
                  child: const LearnHubScreen(),
                ),
              ),
            ],
          ),
"""
if router_text.find(learn_branch) < router_text.find(ai_branch):
    print('router tab order: already applied')
else:
    if ai_branch not in router_text or learn_branch not in router_text:
        raise SystemExit('router tab order: expected branches not found')
    token = '__FLUENTX_AI_BRANCH__'
    router_text = router_text.replace(ai_branch, token, 1)
    router_text = router_text.replace(learn_branch, ai_branch, 1)
    router_text = router_text.replace(token, learn_branch, 1)
    router_text = router_text.replace(
        '// ---- Bottom-nav shell: Home / AI Practice / Progress / Profile ----',
        '// ---- Bottom-nav shell: Home / Learn / Practice / Progress / Profile ----',
    )
    router.write_text(router_text, encoding='utf-8')
    print(f'router tab order: updated {router}')

# 3) Remove the dead notification action. Until an inbox exists, the icon
# intentionally opens notification preferences in Settings.
home = root / 'lib/features/home/presentation/screens/home_screen.dart'
old_notification = """              IconButton(
                onPressed: () {
                  // Notifications inbox ships in Sprint 6.
                },
                icon: Icon(Icons.notifications_none, color: colorScheme.onSurfaceVariant),
              ),
"""
new_notification = """              IconButton(
                tooltip: 'Notification settings',
                onPressed: () => context.push(RoutePaths.settings),
                icon: Icon(Icons.notifications_none, color: colorScheme.onSurfaceVariant),
              ),
"""
replace_once(home, old_notification, new_notification, 'home notification action')

# 4) Give the personalized Learn-path card a real error state instead of an
# endless spinner when the RPC cannot load.
learn = root / 'lib/features/learn/presentation/screens/learn_hub_screen.dart'
old_future = """              builder: (context, snapshot) {
                if (!snapshot.hasData) {
                  return const AppCard(
                    child: Padding(
                      padding: EdgeInsets.symmetric(vertical: AppSpacing.md),
                      child: Center(child: CircularProgressIndicator()),
                    ),
                  );
                }
"""
new_future = """              builder: (context, snapshot) {
                if (snapshot.hasError) {
                  return const AppCard(
                    child: Padding(
                      padding: EdgeInsets.symmetric(vertical: AppSpacing.md),
                      child: Row(
                        children: [
                          Icon(Icons.cloud_off_outlined),
                          SizedBox(width: AppSpacing.md),
                          Expanded(
                            child: Text('Your learning path could not be loaded right now. Pull down or reopen Learn to retry.'),
                          ),
                        ],
                      ),
                    ),
                  );
                }
                if (!snapshot.hasData) {
                  return const AppCard(
                    child: Padding(
                      padding: EdgeInsets.symmetric(vertical: AppSpacing.md),
                      child: Center(child: CircularProgressIndicator()),
                    ),
                  );
                }
"""
replace_once(learn, old_future, new_future, 'learn path error state')

print('FluentX final visual consistency polish applied.')
