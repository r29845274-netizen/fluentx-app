import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/error/failures.dart';
import 'auth_providers.dart';

/// Drives every authentication form action (sign in, sign up, OAuth
/// launch, password reset, sign out).
///
/// Screens watch `authControllerProvider` for `isLoading` (to disable
/// buttons / show a spinner) and listen for `AsyncError` (to surface
/// [Failure.uiMessage] via a snackbar or inline text) — see
/// `login_screen.dart` for the consumption pattern. State updates to
/// [AsyncData] on success; the actual navigation forward happens
/// automatically via the router's redirect reacting to
/// [authStateChangesProvider], not by this controller pushing a route
/// directly — that keeps navigation logic in exactly one place.
class AuthController extends AutoDisposeAsyncNotifier<void> {
  @override
  Future<void> build() async {
    // No initial async work — this notifier only reacts to explicit
    // method calls below.
  }

  Future<void> signInWithEmail({
    required String email,
    required String password,
  }) async {
    state = const AsyncLoading();
    final result = await ref.read(signInWithEmailUseCaseProvider).call(
          email: email,
          password: password,
        );

    state = result.match(
      (failure) => AsyncError<void>(failure, StackTrace.current),
      (_) => const AsyncData(null),
    );
  }

  Future<bool> sendLoginOtp(String email) async {
    state = const AsyncLoading();
    final result = await ref.read(sendLoginOtpUseCaseProvider).call(email);
    return result.match(
      (failure) { state = AsyncError<void>(failure, StackTrace.current); return false; },
      (_) { state = const AsyncData(null); return true; },
    );
  }

  Future<bool> verifyEmailOtp({
    required String email,
    required String token,
    required bool isSignup,
  }) async {
    state = const AsyncLoading();
    final result = await ref.read(verifyEmailOtpUseCaseProvider).call(
      email: email, token: token, isSignup: isSignup,
    );
    return result.match(
      (failure) { state = AsyncError<void>(failure, StackTrace.current); return false; },
      (_) { state = const AsyncData(null); return true; },
    );
  }

  Future<bool> resendEmailOtp({required String email, required bool isSignup}) async {
    state = const AsyncLoading();
    final result = await ref.read(resendEmailOtpUseCaseProvider).call(
      email: email, isSignup: isSignup,
    );
    return result.match(
      (failure) { state = AsyncError<void>(failure, StackTrace.current); return false; },
      (_) { state = const AsyncData(null); return true; },
    );
  }

  Future<bool> signUpWithEmail({
    required String email,
    required String password,
    required String fullName,
  }) async {
    state = const AsyncLoading();
    final result = await ref.read(signUpWithEmailUseCaseProvider).call(
          email: email,
          password: password,
          fullName: fullName,
        );

    return result.match(
      (failure) {
        state = AsyncError<void>(failure, StackTrace.current);
        return false;
      },
      (_) {
        state = const AsyncData(null);
        return true;
      },
    );
  }

  Future<void> signInWithGoogle() async {
    state = const AsyncLoading();
    final result = await ref.read(signInWithGoogleUseCaseProvider).call();

    state = result.match(
      (failure) => AsyncError<void>(failure, StackTrace.current),
      (_) => const AsyncData(null),
    );
  }

  Future<void> signInWithApple() async {
    state = const AsyncLoading();
    final result = await ref.read(signInWithAppleUseCaseProvider).call();

    state = result.match(
      (failure) => AsyncError<void>(failure, StackTrace.current),
      (_) => const AsyncData(null),
    );
  }

  Future<bool> sendPasswordResetEmail(String email) async {
    state = const AsyncLoading();
    final result = await ref.read(sendPasswordResetEmailUseCaseProvider).call(email);

    return result.match(
      (failure) {
        state = AsyncError<void>(failure, StackTrace.current);
        return false;
      },
      (_) {
        state = const AsyncData(null);
        return true;
      },
    );
  }

  Future<void> signOut() async {
    state = const AsyncLoading();
    final result = await ref.read(signOutUseCaseProvider).call();

    state = result.match(
      (failure) => AsyncError<void>(failure, StackTrace.current),
      (_) => const AsyncData(null),
    );
  }
}

final authControllerProvider =
    AutoDisposeAsyncNotifierProvider<AuthController, void>(AuthController.new);
