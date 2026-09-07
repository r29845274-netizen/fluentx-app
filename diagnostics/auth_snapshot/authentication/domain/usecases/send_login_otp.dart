import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failures.dart';
import '../repositories/auth_repository.dart';

class SendLoginOtp {
  SendLoginOtp(this._repository);
  final AuthRepository _repository;

  Future<Either<Failure, Unit>> call(String email) => _repository.sendLoginOtp(email);
}
