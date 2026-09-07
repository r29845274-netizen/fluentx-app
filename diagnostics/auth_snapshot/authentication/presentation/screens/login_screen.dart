import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/error/failures.dart';
import '../../../../core/utils/validators.dart';
import '../../../../routes/route_paths.dart';
import '../../../../shared/widgets/widgets.dart';
import '../../application/providers/auth_controller.dart';
import '../widgets/social_sign_in_button.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _useOtp = true;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    final email = _emailController.text.trim();

    if (_useOtp) {
      final ok = await ref.read(authControllerProvider.notifier).sendLoginOtp(email);
      if (!mounted || !ok) return;
      await context.push(
        '${RoutePaths.verifyEmailOtp}?email=${Uri.encodeComponent(email)}&mode=login',
      );
      return;
    }

    await ref.read(authControllerProvider.notifier).signInWithEmail(
          email: email,
          password: _passwordController.text,
        );
  }

  @override
  Widget build(BuildContext context) {
    ref.listen(authControllerProvider, (previous, next) {
      final error = next.error;
      if (error is Failure) {
        ScaffoldMessenger.of(context)
          ..hideCurrentSnackBar()
          ..showSnackBar(SnackBar(content: Text(error.uiMessage)));
      }
    });

    final isLoading = ref.watch(authControllerProvider).isLoading;

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.base),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: AppSpacing.xl),
                Text('Welcome Back!', style: Theme.of(context).textTheme.displayLarge),
                const SizedBox(height: AppSpacing.sm),
                Text(
                  _useOtp
                      ? 'Log in securely with an email OTP sent to your inbox'
                      : 'Log in to continue your progress',
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                ),
                const SizedBox(height: AppSpacing.xl),
                AppTextField(
                  controller: _emailController,
                  label: 'Email',
                  hint: 'you@gmail.com',
                  keyboardType: TextInputType.emailAddress,
                  textInputAction: _useOtp ? TextInputAction.done : TextInputAction.next,
                  validator: Validators.email,
                  onSubmitted: _useOtp ? (_) => _submit() : null,
                  enabled: !isLoading,
                ),
                if (!_useOtp) ...[
                  const SizedBox(height: AppSpacing.base),
                  AppTextField(
                    controller: _passwordController,
                    label: 'Password',
                    obscureText: true,
                    textInputAction: TextInputAction.done,
                    validator: (v) => Validators.required(v, fieldName: 'Password'),
                    onSubmitted: (_) => _submit(),
                    enabled: !isLoading,
                  ),
                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton(
                      onPressed: isLoading
                          ? null
                          : () => context.push(RoutePaths.forgotPassword),
                      child: const Text('Forgot password?'),
                    ),
                  ),
                ] else
                  const SizedBox(height: AppSpacing.base),
                PrimaryButton(
                  label: _useOtp ? 'Send OTP' : 'Log In',
                  isLoading: isLoading,
                  onPressed: _submit,
                ),
                Center(
                  child: TextButton(
                    onPressed: isLoading ? null : () => setState(() => _useOtp = !_useOtp),
                    child: Text(_useOtp ? 'Use password instead' : 'Use email OTP instead'),
                  ),
                ),
                const SizedBox(height: AppSpacing.md),
                Row(
                  children: [
                    const Expanded(child: Divider()),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.base),
                      child: Text('or continue with', style: Theme.of(context).textTheme.bodySmall),
                    ),
                    const Expanded(child: Divider()),
                  ],
                ),
                const SizedBox(height: AppSpacing.lg),
                SocialSignInButton(
                  label: 'Continue with Google',
                  iconAssetPath: 'assets/icons/google_logo.png',
                  isLoading: isLoading,
                  onPressed: () => ref.read(authControllerProvider.notifier).signInWithGoogle(),
                ),
                const SizedBox(height: AppSpacing.md),
                SocialSignInButton(
                  label: 'Continue with Apple',
                  iconAssetPath: 'assets/icons/apple_logo.png',
                  isLoading: isLoading,
                  onPressed: () => ref.read(authControllerProvider.notifier).signInWithApple(),
                ),
                const SizedBox(height: AppSpacing.xl),
                Center(
                  child: Wrap(
                    alignment: WrapAlignment.center,
                    children: [
                      Text("Don't have an account? ", style: Theme.of(context).textTheme.bodyMedium),
                      GestureDetector(
                        onTap: isLoading ? null : () => context.push(RoutePaths.signup),
                        child: Text(
                          'Sign up',
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                color: Theme.of(context).colorScheme.primary,
                                fontWeight: FontWeight.w600,
                              ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
