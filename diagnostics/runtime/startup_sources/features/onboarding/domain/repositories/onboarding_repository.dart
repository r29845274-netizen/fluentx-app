import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failures.dart';
import '../entities/onboarding_goal.dart';

abstract class OnboardingRepository {
  Future<Either<Failure, Unit>> saveGoal({
    required String userId,
    required OnboardingGoal goal,
  });
}
