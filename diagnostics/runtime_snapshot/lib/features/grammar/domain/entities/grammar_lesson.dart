import 'package:freezed_annotation/freezed_annotation.dart';

part 'grammar_lesson.freezed.dart';

@freezed
class GrammarLesson with _$GrammarLesson {
  const factory GrammarLesson({
    required String id,
    required String title,
    required String explanation,
    required String category,
  }) = _GrammarLesson;
}

@freezed
class GrammarQuestion with _$GrammarQuestion {
  const factory GrammarQuestion({
    required String id,
    required String lessonId,
    required String questionText,
    required List<String> options,
    required int correctIndex,
  }) = _GrammarQuestion;
}
