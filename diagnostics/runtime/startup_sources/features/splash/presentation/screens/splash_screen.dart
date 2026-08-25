import 'package:flutter/material.dart';

/// FluentX's splash screen.
///
/// Purely presentational — it does not decide where to navigate next.
/// The router's `redirect` callback (see `app_router.dart`) reacts to
/// [authStatusProvider] resolving from [AuthStatus.unknown] and
/// automatically routes to onboarding, login, or home. This screen
/// only needs to render briefly while that resolves.
class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 72,
              height: 72,
              decoration: BoxDecoration(
                color: colorScheme.primary,
                borderRadius: BorderRadius.circular(20),
              ),
              child: Icon(Icons.graphic_eq, color: colorScheme.onPrimary, size: 36),
            ),
            const SizedBox(height: 16),
            Text('FluentX', style: Theme.of(context).textTheme.headlineMedium),
          ],
        ),
      ),
    );
  }
}
