import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/error/failures.dart';
import '../../../../shared/widgets/widgets.dart';
import '../../application/providers/auth_controller.dart';

class OtpVerificationScreen extends ConsumerStatefulWidget {
  const OtpVerificationScreen({
    super.key,
    required this.email,
    required this.isSignup,
  });

  final String email;
  final bool isSignup;

  @override
  ConsumerState<OtpVerificationScreen> createState() => _OtpVerificationScreenState();
}

class _OtpVerificationScreenState extends ConsumerState<OtpVerificationScreen> {
  final _otpController = TextEditingController();
  Timer? _timer;
  int _secondsRemaining = 60;

  @override
  void initState() {
    super.initState();
    _startCooldown();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _otpController.dispose();
    super.dispose();
  }

  void _startCooldown() {
    _timer?.cancel();
    setState(() => _secondsRemaining = 60);
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) return;
      if (_secondsRemaining <= 1) {
        timer.cancel();
        setState(() => _secondsRemaining = 0);
      } else {
        setState(() => _secondsRemaining--);
      }
    });
  }

  Future<void> _verify() async {
    final token = _otpController.text.trim();
    if (token.length != 6) {
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(const SnackBar(content: Text('Enter the 6-digit OTP.')));
      return;
    }

    await ref.read(authControllerProvider.notifier).verifyEmailOtp(
          email: widget.email,
          token: token,
          isSignup: widget.isSignup,
        );
  }

  Future<void> _resend() async {
    if (_secondsRemaining > 0) return;
    final ok = await ref.read(authControllerProvider.notifier).resendEmailOtp(
          email: widget.email,
          isSignup: widget.isSignup,
        );
    if (!mounted) return;
    if (ok) {
      _otpController.clear();
      _startCooldown();
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(const SnackBar(content: Text('A new OTP has been sent.')));
    }
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
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(),
      body: SafeArea(
        top: false,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.base),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: AppSpacing.md),
              Text('Verify your email', style: Theme.of(context).textTheme.displayLarge),
              const SizedBox(height: AppSpacing.sm),
              Text(
                'We sent a 6-digit email OTP to ${widget.email}',
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: colorScheme.onSurfaceVariant,
                    ),
              ),
              const SizedBox(height: AppSpacing.xl),
              TextField(
                controller: _otpController,
                enabled: !isLoading,
                autofocus: true,
                keyboardType: TextInputType.number,
                textInputAction: TextInputAction.done,
                maxLength: 6,
                inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      letterSpacing: 10,
                      fontWeight: FontWeight.w700,
                    ),
                decoration: const InputDecoration(
                  labelText: 'OTP code',
                  hintText: '000000',
                  counterText: '',
                ),
                onSubmitted: (_) => _verify(),
              ),
              const SizedBox(height: AppSpacing.lg),
              PrimaryButton(
                label: 'Verify OTP',
                isLoading: isLoading,
                onPressed: _verify,
              ),
              const SizedBox(height: AppSpacing.base),
              Center(
                child: TextButton(
                  onPressed: isLoading || _secondsRemaining > 0 ? null : _resend,
                  child: Text(
                    _secondsRemaining > 0
                        ? 'Resend OTP in ${_secondsRemaining}s'
                        : 'Resend OTP',
                  ),
                ),
              ),
              const SizedBox(height: AppSpacing.sm),
              Center(
                child: Text(
                  'Check Inbox, Spam or Promotions. You can resend the email OTP when the timer ends.',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: colorScheme.onSurfaceVariant,
                      ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
