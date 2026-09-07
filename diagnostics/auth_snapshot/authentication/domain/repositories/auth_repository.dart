import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failures.dart';
import '../entities/app_user.dart';

/// Abstract contract for authentication operations.
///
/// Lives in the domain layer with zero implementation details —
/// `AuthRepositoryImpl` (data layer) is the only class that knows
/// about Supabase. Use cases and the application layer depend only on
/// this interface, which is what makes swapping backends or writing
/// unit tests with a fake repository possible.
abstract class AuthRepository {
  /// Emits the current user whenever auth state changes (sign in, sign
  /// out, token refresh), and `null` when signed out. Used to drive
  /// [authStatusProvider] in `core/router/auth_status.dart`.
  Stream<AppUser?> get authStateChanges;

  AppUser? get currentUser;

  Future<Either<Failure, AppUser>> signInWithEmail({
    required String email,
    required String password,
  });

  Future<Either<Failure, AppUser>> signUpWithEmail({
    required String email,
    required String password,
    required String fullName,
  });

  Future<Either<Failure, Unit>> sendLoginOtp(String email);

  Future<Either<Failure, AppUser>> verifyEmailOtp({
    required String email,
    required String token,
    required bool isSignup,
  });

  Future<Either<Failure, Unit>> resendEmailOtp({
    required String email,
    required bool isSignup,
  });

  /// Launches the Google OAuth redirect flow. This does NOT resolve
  /// with the signed-in user — Supabase's mobile OAuth flow completes
  /// via a deep-link redirect back into the app, which fires
  /// [authStateChanges] asynchronously. The `Either<Failure, Unit>`
  /// here only reports whether the redirect was launched successfully.
  Future<Either<Failure, Unit>> signInWithGoogle();

  /// Same redirect-based flow as [signInWithGoogle], for Apple OAuth.
  Future<Either<Failure, Unit>> signInWithApple();

  Future<Either<Failure, Unit>> sendPasswordResetEmail(String email);

  Future<Either<Failure, Unit>> signOut();
}
