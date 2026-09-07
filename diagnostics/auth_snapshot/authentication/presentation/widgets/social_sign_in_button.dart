import 'package:flutter/material.dart';

import '../../../../core/constants/app_radius.dart';
import '../../../../core/constants/app_spacing.dart';

/// Outlined, icon + label button used for "Continue with Google" /
/// "Continue with Apple" on the login and signup screens.
///
/// Uses `Image.asset` for the provider logo rather than a generic
/// Lucide icon — Google/Apple's brand marks are recognizable and
/// expected here; a generic icon would look off-brand and reduce
/// trust at exactly the moment a new user is deciding whether to sign
/// up.
class SocialSignInButton extends StatelessWidget {
  const SocialSignInButton({
    required this.label,
    required this.iconAssetPath,
    required this.onPressed,
    super.key,
    this.isLoading = false,
  });

  final String label;
  final String iconAssetPath;
  final VoidCallback? onPressed;
  final bool isLoading;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return SizedBox(
      width: double.infinity,
      child: OutlinedButton(
        onPressed: isLoading ? null : onPressed,
        style: OutlinedButton.styleFrom(
          side: BorderSide(color: colorScheme.outline, width: 1.5),
          shape: RoundedRectangleBorder(borderRadius: AppRadius.mdAll),
        ),
        child: isLoading
            ? SizedBox(
                height: 20,
                width: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2.5,
                  valueColor: AlwaysStoppedAnimation<Color>(colorScheme.onSurface),
                ),
              )
            : Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Image.asset(iconAssetPath, height: 20, width: 20),
                  const SizedBox(width: AppSpacing.sm),
                  Text(label, style: Theme.of(context).textTheme.labelLarge),
                ],
              ),
      ),
    );
  }
}
