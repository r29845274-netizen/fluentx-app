import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failures.dart';
import '../entities/onboarding_goal.dart';
import '../repositories/onboarding_repository.dart';

class SaveLearningGoal {
  const SaveLearningGoal(this._repository);
  final OnboardingRepository _repository;

  Future<Either<Failure, Unit>> call({
    required String userId,
    required OnboardingGoal goal,
  }) {
    return _repository.saveGoal(userId: userId, goal: goal);
  }
}
