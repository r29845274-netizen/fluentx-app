import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:purchases_flutter/purchases_flutter.dart';

import '../core/theme/app_theme.dart';
import '../core/theme/theme_mode_provider.dart';
import '../features/authentication/application/providers/auth_providers.dart';
import '../routes/app_router.dart';

/// Root widget of the FluentX app.
///
/// Kept intentionally thin — its only job is wiring the router and
/// theme providers into [MaterialApp.router]. All actual app logic
/// lives in feature modules.
class FluentXApp extends ConsumerWidget {
  const FluentXApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);
    final themeMode = ref.watch(themeModeProvider);

    // Keeps RevenueCat's customer identity in sync with Supabase auth,
    // so a purchase made on one device is recognized after signing in
    // on another. `Purchases.configure` in main.dart may not have run
    // (RevenueCat key not set in dev) — guarded so this never crashes
    // local development.
    ref.listen(authStateChangesProvider, (previous, next) {
      final user = next.value;
      if (user != null) {
        Purchases.logIn(user.id).then<void>((_) {}, onError: (_, __) {});
      } else if (previous?.value != null) {
        Purchases.logOut().then<void>((_) {}, onError: (_, __) {});
      }
    });

    return MaterialApp.router(
      title: 'Fluent X',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: themeMode,
      routerConfig: router,
    );
  }
}
