import 'package:fpdart/fpdart.dart';

import '../../../../core/error/exceptions.dart';
import '../../../../core/error/failures.dart';
import '../../domain/entities/onboarding_goal.dart';
import '../../domain/repositories/onboarding_repository.dart';
import '../datasources/onboarding_remote_datasource.dart';

class OnboardingRepositoryImpl implements OnboardingRepository {
  OnboardingRepositoryImpl(this._remoteDataSource);
  final OnboardingRemoteDataSource _remoteDataSource;

  @override
  Future<Either<Failure, Unit>> saveGoal({
    required String userId,
    required OnboardingGoal goal,
  }) async {
    try {
      await _remoteDataSource.saveGoal(userId: userId, goal: goal);
      return right(unit);
    } on ServerException catch (e) {
      return left(Failure.server(message: e.message));
    } catch (e) {
      return left(const Failure.unexpected());
    }
  }
}
