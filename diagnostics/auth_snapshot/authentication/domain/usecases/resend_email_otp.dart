import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failures.dart';
import '../repositories/auth_repository.dart';

class ResendEmailOtp {
  ResendEmailOtp(this._repository);
  final AuthRepository _repository;

  Future<Either<Failure, Unit>> call({
    required String email,
    required bool isSignup,
  }) => _repository.resendEmailOtp(email: email, isSignup: isSignup);
}
