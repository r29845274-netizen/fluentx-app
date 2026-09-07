import 'package:supabase_flutter/supabase_flutter.dart' as supabase;

import '../../../../core/error/exceptions.dart';
import '../../domain/entities/app_user.dart';
import '../models/app_user_model.dart';

abstract class AuthRemoteDataSource {
  Stream<AppUser?> get authStateChanges;

  AppUser? get currentUser;

  Future<AppUser> signInWithEmail({required String email, required String password});

  Future<AppUser> signUpWithEmail({
    required String email,
    required String password,
    required String fullName,
  });

  Future<void> sendLoginOtp(String email);

  Future<AppUser> verifyEmailOtp({
    required String email,
    required String token,
    required bool isSignup,
  });

  Future<void> resendEmailOtp({
    required String email,
    required bool isSignup,
  });

  Future<void> signInWithGoogle();

  Future<void> signInWithApple();

  Future<void> sendPasswordResetEmail(String email);

  Future<void> signOut();
}

/// The ONLY class permitted to import `supabase_flutter`'s auth APIs
/// directly. Every other layer (domain, application, presentation)
/// depends on the abstract [AuthRemoteDataSource] / [AuthRepository]
/// contracts instead, so Supabase could be swapped for a different
/// backend by rewriting only this file and its sibling repository impl.
class AuthRemoteDataSourceImpl implements AuthRemoteDataSource {
  AuthRemoteDataSourceImpl(this._client);

  final supabase.SupabaseClient _client;

  /// Deep-link scheme registered in AndroidManifest.xml / Info.plist
  /// for OAuth redirects to land back in the app. See
  /// SPRINT_1_AUTH_README.md for the exact platform config.
  static const _oauthRedirectUri = 'io.fluentx.app://login-callback';

  @override
  Stream<AppUser?> get authStateChanges {
    return _client.auth.onAuthStateChange.map((data) {
      return data.session?.user.toEntity();
    });
  }

  @override
  AppUser? get currentUser => _client.auth.currentUser?.toEntity();

  @override
  Future<AppUser> signInWithEmail({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _client.auth.signInWithPassword(
        email: email,
        password: password,
      );
      final user = response.user;
      if (user == null) {
        throw const AuthException('Sign in failed. Please try again.');
      }
      return user.toEntity();
    } on supabase.AuthException catch (e) {
      throw AuthException(e.message);
    } catch (e) {
      throw ServerException(e.toString());
    }
  }

  @override
  Future<AppUser> signUpWithEmail({
    required String email,
    required String password,
    required String fullName,
  }) async {
    try {
      final response = await _client.auth.signUp(
        email: email,
        password: password,
        data: {'full_name': fullName},
      );
      final user = response.user;
      if (user == null) {
        throw const AuthException('Sign up failed. Please try again.');
      }
      return user.toEntity();
    } on supabase.AuthException catch (e) {
      throw AuthException(e.message);
    } catch (e) {
      throw ServerException(e.toString());
    }
  }

  @override
  Future<void> sendLoginOtp(String email) async {
    try {
      await _client.auth.signInWithOtp(
        email: email,
        shouldCreateUser: false,
      );
    } on supabase.AuthException catch (e) {
      throw AuthException(e.message);
    } catch (e) {
      throw ServerException(e.toString());
    }
  }

  @override
  Future<AppUser> verifyEmailOtp({
    required String email,
    required String token,
    required bool isSignup,
  }) async {
    try {
      final response = await _client.auth.verifyOTP(
        email: email,
        token: token,
        type: isSignup ? supabase.OtpType.signup : supabase.OtpType.email,
      );
      final user = response.user;
      if (user == null || response.session == null) {
        throw const AuthException('OTP verification failed. Please request a new code.');
      }
      return user.toEntity();
    } on supabase.AuthException catch (e) {
      throw AuthException(e.message);
    } catch (e) {
      throw ServerException(e.toString());
    }
  }

  @override
  Future<void> resendEmailOtp({
    required String email,
    required bool isSignup,
  }) async {
    try {
      if (isSignup) {
        await _client.auth.resend(
          type: supabase.OtpType.signup,
          email: email,
        );
      } else {
        await _client.auth.signInWithOtp(
          email: email,
          shouldCreateUser: false,
        );
      }
    } on supabase.AuthException catch (e) {
      throw AuthException(e.message);
    } catch (e) {
      throw ServerException(e.toString());
    }
  }

  @override
  Future<void> signInWithGoogle() async {
    try {
      await _client.auth.signInWithOAuth(
        supabase.OAuthProvider.google,
        redirectTo: _oauthRedirectUri,
        authScreenLaunchMode: supabase.LaunchMode.externalApplication,
      );
    } on supabase.AuthException catch (e) {
      throw AuthException(e.message);
    } catch (e) {
      throw ServerException(e.toString());
    }
  }

  @override
  Future<void> signInWithApple() async {
    try {
      await _client.auth.signInWithOAuth(
        supabase.OAuthProvider.apple,
        redirectTo: _oauthRedirectUri,
        authScreenLaunchMode: supabase.LaunchMode.externalApplication,
      );
    } on supabase.AuthException catch (e) {
      throw AuthException(e.message);
    } catch (e) {
      throw ServerException(e.toString());
    }
  }

  @override
  Future<void> sendPasswordResetEmail(String email) async {
    try {
      await _client.auth.resetPasswordForEmail(
        email,
        redirectTo: '$_oauthRedirectUri/reset-password',
      );
    } on supabase.AuthException catch (e) {
      throw AuthException(e.message);
    } catch (e) {
      throw ServerException(e.toString());
    }
  }

  @override
  Future<void> signOut() async {
    try {
      await _client.auth.signOut();
    } on supabase.AuthException catch (e) {
      throw AuthException(e.message);
    } catch (e) {
      throw ServerException(e.toString());
    }
  }
}
