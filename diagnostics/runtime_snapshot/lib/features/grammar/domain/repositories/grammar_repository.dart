import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failures.dart';
import '../entities/grammar_lesson.dart';

abstract class GrammarRepository {
  Future<Either<Failure, List<GrammarLesson>>> getLessons();

  Future<Either<Failure, List<GrammarQuestion>>> getQuestions(String lessonId);

  /// Records one wrong answer against [category] for mistake-pattern
  /// tracking (feeds Communication DNA's Grammar Accuracy component).
  Future<Either<Failure, Unit>> recordMistake({
    required String userId,
    required String category,
  });
}
