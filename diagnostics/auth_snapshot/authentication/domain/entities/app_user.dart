import 'package:freezed_annotation/freezed_annotation.dart';

part 'app_user.freezed.dart';

/// Pure domain entity representing an authenticated FluentX user.
///
/// Contains zero Supabase/Flutter dependencies by design — the data
/// layer's `AppUserModel` is responsible for translating to/from this
/// shape, so swapping the backend later would never touch this file.
@freezed
class AppUser with _$AppUser {
  const factory AppUser({
    required String id,
    required String email,
    String? fullName,
    String? avatarUrl,
    required bool isEmailVerified,
    required DateTime createdAt,
  }) = _AppUser;
}
