import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/supabase_provider.dart';
import '../../../../core/router/onboarding_status_provider.dart';
import '../../../authentication/application/providers/auth_providers.dart';
import '../../data/datasources/onboarding_remote_datasource.dart';
import '../../data/repositories/onboarding_repository_impl.dart';
import '../../domain/entities/onboarding_goal.dart';
import '../../domain/repositories/onboarding_repository.dart';
import '../../domain/usecases/save_learning_goal.dart';

final onboardingRemoteDataSourceProvider = Provider<OnboardingRemoteDataSource>((ref) {
  return OnboardingRemoteDataSourceImpl(ref.watch(supabaseClientProvider));
});

final onboardingRepositoryProvider = Provider<OnboardingRepository>((ref) {
  return OnboardingRepositoryImpl(ref.watch(onboardingRemoteDataSourceProvider));
});

final saveLearningGoalUseCaseProvider = Provider<SaveLearningGoal>((ref) {
  return SaveLearningGoal(ref.watch(onboardingRepositoryProvider));
});

/// Drives the onboarding flow's final step: persist the chosen goal,
/// then mark onboarding complete (Hive flag from Sprint 1 Part 3) so
/// the router's redirect sends the user into the app.
class OnboardingController extends AutoDisposeAsyncNotifier<void> {
  @override
  Future<void> build() async {}

  Future<void> completeOnboarding(OnboardingGoal? goal) async {
    state = const AsyncLoading();

    final userId = ref.read(authStateChangesProvider).value?.id;
    if (userId == null || goal == null) {
      // Skipped goal selection, or not signed in somehow — still let
      // the user into the app rather than trapping them on onboarding.
      ref.read(onboardingCompleteProvider.notifier).markComplete();
      state = const AsyncData(null);
      return;
    }

    final result = await ref.read(saveLearningGoalUseCaseProvider).call(userId: userId, goal: goal);

    result.match(
      (failure) {
        // Even if saving the goal fails (e.g. offline), don't block
        // the user from entering the app — they can set it later from
        // Settings. Log the failure via state so the UI can inform them.
        ref.read(onboardingCompleteProvider.notifier).markComplete();
        state = AsyncError<void>(failure, StackTrace.current);
      },
      (_) {
        ref.read(onboardingCompleteProvider.notifier).markComplete();
        state = const AsyncData(null);
      },
    );
  }
}

final onboardingControllerProvider =
    AutoDisposeAsyncNotifierProvider<OnboardingController, void>(OnboardingController.new);
