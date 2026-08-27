import 'package:flutter/material.dart';

import '../../../core/constants/app_spacing.dart';
import '../buttons/primary_button.dart';

/// Full-section error state — shown when a data fetch fails
/// (network error, AI service unavailable, etc.).
///
/// Deliberately avoids generic "Oops! Something went wrong" copy —
/// callers should pass a specific, human [message]. [onRetry] is
/// optional; omit it for errors that aren't retryable (e.g. a 403).
class ErrorStateWidget extends StatelessWidget {
  const ErrorStateWidget({
    super.key,
    this.title = 'Something interrupted this',
    this.message = 'We couldn\'t load this right now. Please try again.',
    this.onRetry,
    this.icon = Icons.wifi_off,
  });

  final String title;
  final String message;
  final VoidCallback? onRetry;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 56, color: colorScheme.onSurfaceVariant),
            const SizedBox(height: AppSpacing.base),
            Text(
              title,
              style: Theme.of(context).textTheme.headlineSmall,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              message,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: colorScheme.onSurfaceVariant,
                  ),
              textAlign: TextAlign.center,
            ),
            if (onRetry != null) ...[
              const SizedBox(height: AppSpacing.lg),
              PrimaryButton(
                label: 'Try again',
                icon: Icons.refresh,
                fullWidth: false,
                onPressed: onRetry,
              ),
            ],
          ],
        ),
      ),
    );
  }
}
