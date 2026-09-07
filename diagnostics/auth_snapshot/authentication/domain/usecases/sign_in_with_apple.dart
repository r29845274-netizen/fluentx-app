import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failures.dart';
import '../repositories/auth_repository.dart';

/// Launches the Apple OAuth redirect flow. Same asynchronous
/// completion model as [SignInWithGoogle] — see
/// [AuthRepository.signInWithApple].
///
/// Required for App Store submission if/when FluentX ships on iOS
/// (any app offering third-party social sign-in must also offer Apple
/// Sign-In). Scaffolded now even though launch is Android-first.
class SignInWithApple {
  const SignInWithApple(this._repository);

  final AuthRepository _repository;

  Future<Either<Failure, Unit>> call() {
    return _repository.signInWithApple();
  }
}
