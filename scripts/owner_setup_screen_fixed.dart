import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/network/supabase_provider.dart';
import '../../../../core/utils/validators.dart';
import '../../../../routes/route_paths.dart';
import '../../../../shared/widgets/widgets.dart';

class OwnerSetupScreen extends ConsumerStatefulWidget {
  const OwnerSetupScreen({super.key});
  @override
  ConsumerState<OwnerSetupScreen> createState() => _OwnerSetupScreenState();
}

class _OwnerSetupScreenState extends ConsumerState<OwnerSetupScreen> {
  final _formKey = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _loading = true;
  bool _ready = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _checkStatus();
  }

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _checkStatus() async {
    try {
      final client = ref.read(supabaseClientProvider);
      final response = await client.functions.invoke('owner-bootstrap-status');
      if (!mounted) return;
      if (response.status == 404) {
        context.go(RoutePaths.login);
        return;
      }
      final data = response.data;
      if (response.status != 200 || data is! Map ||
          data['configuration_missing'] == true ||
          data['setup_required'] != true) {
        setState(() {
          _error = 'Owner setup is not available. Check the server configuration.';
          _loading = false;
        });
        return;
      }
      setState(() { _ready = true; _loading = false; });
    } catch (_) {
      if (mounted) setState(() {
        _error = 'Unable to check owner setup. Check your connection and retry.';
        _loading = false;
      });
    }
  }

  Future<void> _claim() async {
    if (_loading || !_ready || !_formKey.currentState!.validate()) return;
    setState(() { _loading = true; _error = null; });
    final client = ref.read(supabaseClientProvider);
    bool established = false;
    try {
      final result = await client.functions.invoke('password-login', body: {
        'email': _email.text.trim().toLowerCase(),
        'password': _password.text,
      });
      if (result.status == 429) {
        throw const _OwnerSetupException('Too many attempts. Please wait before trying again.');
      }
      if (result.status != 200 || result.data is! Map) {
        throw const _OwnerSetupException('Sign in failed. Check your existing email and password.');
      }
      final token = (result.data as Map)['refresh_token'];
      if (token is! String || token.isEmpty) {
        throw const _OwnerSetupException('Could not establish a login session.');
      }
      final signed = await client.auth.setSession(token);
      if (signed.user == null || signed.session == null ||
          signed.user!.emailConfirmedAt == null ||
          signed.user!.email?.toLowerCase() != _email.text.trim().toLowerCase()) {
        throw const _OwnerSetupException('A verified account is required.');
      }
      established = true;
      final claim = await client.functions.invoke('owner-bootstrap');
      if (claim.status != 200 || claim.data is! Map ||
          (claim.data as Map)['ok'] != true) {
        throw const _OwnerSetupException(
          'Owner claim was not approved. Use the verified email configured as OWNER_EMAIL.',
        );
      }
      if (mounted) context.go(RoutePaths.adminConsole);
    } catch (e) {
      if (established) {
        try { await client.auth.signOut(); } catch (_) {}
      }
      if (mounted) setState(() {
        _error = e is _OwnerSetupException
            ? e.message
            : 'Could not complete owner setup. Check your connection and try again.';
      });
    } finally {
      if (mounted) setState(() { _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading && !_ready) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
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
                Text('Set up FluentX owner', style: Theme.of(context).textTheme.displayLarge),
                const SizedBox(height: AppSpacing.sm),
                const Text('Use your existing verified FluentX account to securely claim the first owner. No second signup or signup OTP is needed.'),
                const SizedBox(height: AppSpacing.xl),
                AppTextField(
                  controller: _email,
                  label: 'Existing verified owner email',
                  keyboardType: TextInputType.emailAddress,
                  validator: Validators.email,
                  enabled: !_loading && _ready,
                ),
                const SizedBox(height: AppSpacing.base),
                AppTextField(
                  controller: _password,
                  label: 'Existing account password',
                  obscureText: true,
                  validator: (value) => Validators.required(value, fieldName: 'Password'),
                  enabled: !_loading && _ready,
                ),
                if (_error != null) ...[
                  const SizedBox(height: AppSpacing.md),
                  Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
                ],
                const SizedBox(height: AppSpacing.lg),
                PrimaryButton(
                  label: 'Sign in & verify owner',
                  isLoading: _loading,
                  onPressed: _ready ? _claim : null,
                ),
                const SizedBox(height: AppSpacing.sm),
                Center(
                  child: TextButton(
                    onPressed: _loading ? null : () => context.go(RoutePaths.login),
                    child: const Text('Return to login'),
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

class _OwnerSetupException implements Exception {
  const _OwnerSetupException(this.message);
  final String message;
}
