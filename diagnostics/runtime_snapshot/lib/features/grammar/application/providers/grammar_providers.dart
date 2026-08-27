import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/supabase_provider.dart';
import '../../data/datasources/grammar_remote_datasource.dart';
import '../../data/repositories/grammar_repository_impl.dart';
import '../../domain/entities/grammar_lesson.dart';
import '../../domain/repositories/grammar_repository.dart';
import '../../domain/usecases/get_grammar_lessons.dart';
import '../../domain/usecases/get_grammar_questions.dart';
import '../../domain/usecases/record_grammar_mistake.dart';

final grammarRemoteDataSourceProvider = Provider<GrammarRemoteDataSource>((ref) {
  return GrammarRemoteDataSourceImpl(ref.watch(supabaseClientProvider));
});

final grammarRepositoryProvider = Provider<GrammarRepository>((ref) {
  return GrammarRepositoryImpl(ref.watch(grammarRemoteDataSourceProvider));
});

final getGrammarLessonsUseCaseProvider = Provider<GetGrammarLessons>((ref) {
  return GetGrammarLessons(ref.watch(grammarRepositoryProvider));
});

final getGrammarQuestionsUseCaseProvider = Provider<GetGrammarQuestions>((ref) {
  return GetGrammarQuestions(ref.watch(grammarRepositoryProvider));
});

final recordGrammarMistakeUseCaseProvider = Provider<RecordGrammarMistake>((ref) {
  return RecordGrammarMistake(ref.watch(grammarRepositoryProvider));
});

final grammarLessonsProvider = FutureProvider.autoDispose<List<GrammarLesson>>((ref) async {
  final result = await ref.watch(getGrammarLessonsUseCaseProvider).call();
  return result.match((failure) => throw failure, (lessons) => lessons);
});

/// `.family` — one cached question list per lesson id, since the user
/// may open several lessons in one Grammar session.
final grammarQuestionsProvider =
    FutureProvider.autoDispose.family<List<GrammarQuestion>, String>((ref, lessonId) async {
  final result = await ref.watch(getGrammarQuestionsUseCaseProvider).call(lessonId);
  return result.match((failure) => throw failure, (questions) => questions);
});
