import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failures.dart';
import '../entities/app_user.dart';
import '../repositories/auth_repository.dart';

class VerifyEmailOtp {
  VerifyEmailOtp(this._repository);
  final AuthRepository _repository;

  Future<Either<Failure, AppUser>> call({
    required String email,
    required String token,
    required bool isSignup,
  }) => _repository.verifyEmailOtp(email: email, token: token, isSignup: isSignup);
}
