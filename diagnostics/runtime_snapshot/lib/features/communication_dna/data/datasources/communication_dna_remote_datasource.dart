import 'package:supabase_flutter/supabase_flutter.dart' as supabase;

import '../../../../core/error/exceptions.dart';
import '../../domain/entities/communication_dna.dart';
import '../models/communication_dna_model.dart';

abstract class CommunicationDnaRemoteDataSource {
  Future<CommunicationDna> getDna(String userId);
}

class CommunicationDnaRemoteDataSourceImpl implements CommunicationDnaRemoteDataSource {
  CommunicationDnaRemoteDataSourceImpl(this._client);
  final supabase.SupabaseClient _client;

  @override
  Future<CommunicationDna> getDna(String userId) async {
    try {
      final rows = await _client.rpc<List<dynamic>>(
        'get_communication_dna',
        params: {'p_user_id': userId},
      );
      if (rows.isEmpty) {
        throw const ServerException('No Communication DNA data available yet.');
      }
      return (rows.first as Map<String, dynamic>).toCommunicationDna();
    } on supabase.PostgrestException catch (e) {
      throw ServerException(e.message);
    } catch (e) {
      throw ServerException(e.toString());
    }
  }
}
