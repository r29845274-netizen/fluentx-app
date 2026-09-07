import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failures.dart';
import '../repositories/auth_repository.dart';

/// Launches the Google OAuth redirect flow (sign in, or sign up on
/// first use). The resulting session arrives asynchronously via
/// [AuthRepository.authStateChanges] once the deep-link redirect
/// completes — see the doc comment on
/// [AuthRepository.signInWithGoogle] for why this doesn't return the
/// user directly.
class SignInWithGoogle {
  const SignInWithGoogle(this._repository);

  final AuthRepository _repository;

  Future<Either<Failure, Unit>> call() {
    return _repository.signInWithGoogle();
  }
}
