import 'package:fpdart/fpdart.dart';

import '../../../../core/error/exceptions.dart';
import '../../../../core/error/failures.dart';
import '../../domain/entities/app_user.dart';
import '../../domain/repositories/auth_repository.dart';
import '../datasources/auth_remote_datasource.dart';

/// Concrete [AuthRepository] backed by [AuthRemoteDataSource].
///
/// Its only real job is the exception → [Failure] translation boundary
/// — every datasource call is wrapped in a try/catch so nothing above
/// this layer ever needs a try/catch for auth operations.
class AuthRepositoryImpl implements AuthRepository {
  AuthRepositoryImpl(this._remoteDataSource);

  final AuthRemoteDataSource _remoteDataSource;

  @override
  Stream<AppUser?> get authStateChanges => _remoteDataSource.authStateChanges;

  @override
  AppUser? get currentUser => _remoteDataSource.currentUser;

  @override
  Future<Either<Failure, AppUser>> signInWithEmail({
    required String email,
    required String password,
  }) async {
    try {
      final user = await _remoteDataSource.signInWithEmail(
        email: email,
        password: password,
      );
      return right(user);
    } on AuthException catch (e) {
      return left(Failure.auth(message: e.message));
    } on ServerException catch (e) {
      return left(Failure.server(message: e.message));
    } catch (e) {
      return left(const Failure.unexpected());
    }
  }

  @override
  Future<Either<Failure, AppUser>> signUpWithEmail({
    required String email,
    required String password,
    required String fullName,
  }) async {
    try {
      final user = await _remoteDataSource.signUpWithEmail(
        email: email,
        password: password,
        fullName: fullName,
      );
      return right(user);
    } on AuthException catch (e) {
      return left(Failure.auth(message: e.message));
    } on ServerException catch (e) {
      return left(Failure.server(message: e.message));
    } catch (e) {
      return left(const Failure.unexpected());
    }
  }

  @override
  Future<Either<Failure, Unit>> sendLoginOtp(String email) async {
    try {
      await _remoteDataSource.sendLoginOtp(email);
      return right(unit);
    } on AuthException catch (e) {
      return left(Failure.auth(message: e.message));
    } on ServerException catch (e) {
      return left(Failure.server(message: e.message));
    } catch (e) {
      return left(const Failure.unexpected());
    }
  }

  @override
  Future<Either<Failure, AppUser>> verifyEmailOtp({
    required String email,
    required String token,
    required bool isSignup,
  }) async {
    try {
      final user = await _remoteDataSource.verifyEmailOtp(
        email: email,
        token: token,
        isSignup: isSignup,
      );
      return right(user);
    } on AuthException catch (e) {
      return left(Failure.auth(message: e.message));
    } on ServerException catch (e) {
      return left(Failure.server(message: e.message));
    } catch (e) {
      return left(const Failure.unexpected());
    }
  }

  @override
  Future<Either<Failure, Unit>> resendEmailOtp({
    required String email,
    required bool isSignup,
  }) async {
    try {
      await _remoteDataSource.resendEmailOtp(email: email, isSignup: isSignup);
      return right(unit);
    } on AuthException catch (e) {
      return left(Failure.auth(message: e.message));
    } on ServerException catch (e) {
      return left(Failure.server(message: e.message));
    } catch (e) {
      return left(const Failure.unexpected());
    }
  }

  @override
  Future<Either<Failure, Unit>> signInWithGoogle() async {
    try {
      await _remoteDataSource.signInWithGoogle();
      return right(unit);
    } on AuthException catch (e) {
      return left(Failure.auth(message: e.message));
    } on ServerException catch (e) {
      return left(Failure.server(message: e.message));
    } catch (e) {
      return left(const Failure.unexpected());
    }
  }

  @override
  Future<Either<Failure, Unit>> signInWithApple() async {
    try {
      await _remoteDataSource.signInWithApple();
      return right(unit);
    } on AuthException catch (e) {
      return left(Failure.auth(message: e.message));
    } on ServerException catch (e) {
      return left(Failure.server(message: e.message));
    } catch (e) {
      return left(const Failure.unexpected());
    }
  }

  @override
  Future<Either<Failure, Unit>> sendPasswordResetEmail(String email) async {
    try {
      await _remoteDataSource.sendPasswordResetEmail(email);
      return right(unit);
    } on AuthException catch (e) {
      return left(Failure.auth(message: e.message));
    } on ServerException catch (e) {
      return left(Failure.server(message: e.message));
    } catch (e) {
      return left(const Failure.unexpected());
    }
  }

  @override
  Future<Either<Failure, Unit>> signOut() async {
    try {
      await _remoteDataSource.signOut();
      return right(unit);
    } on ServerException catch (e) {
      return left(Failure.server(message: e.message));
    } catch (e) {
      return left(const Failure.unexpected());
    }
  }
}
