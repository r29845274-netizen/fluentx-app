import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failures.dart';
import '../repositories/auth_repository.dart';

/// Triggers Supabase's password-reset email flow, which deep-links the
/// user back into the app (see `app_router.dart` deep link handling,
/// added when the reset-password screen ships).
class SendPasswordResetEmail {
  const SendPasswordResetEmail(this._repository);

  final AuthRepository _repository;

  Future<Either<Failure, Unit>> call(String email) {
    return _repository.sendPasswordResetEmail(email);
  }
}
