import 'package:supabase_flutter/supabase_flutter.dart' as supabase;

import '../../../../core/error/exceptions.dart';
import '../../domain/entities/onboarding_goal.dart';

abstract class OnboardingRemoteDataSource {
  Future<void> saveGoal({required String userId, required OnboardingGoal goal});
}

/// Writes into the same `user_home_stats` row the Home feature reads
/// from — no separate onboarding table needed for a single column.
class OnboardingRemoteDataSourceImpl implements OnboardingRemoteDataSource {
  OnboardingRemoteDataSourceImpl(this._client);
  final supabase.SupabaseClient _client;

  @override
  Future<void> saveGoal({required String userId, required OnboardingGoal goal}) async {
    try {
      await _client
          .from('user_home_stats')
          .upsert({'user_id': userId, 'learning_goal': goal.storageValue});
    } on supabase.PostgrestException catch (e) {
      throw ServerException(e.message);
    } catch (e) {
      throw ServerException(e.toString());
    }
  }
}
