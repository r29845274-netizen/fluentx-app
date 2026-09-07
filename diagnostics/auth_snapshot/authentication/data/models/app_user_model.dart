import 'package:supabase_flutter/supabase_flutter.dart' as supabase;

import '../../domain/entities/app_user.dart';

/// Data-layer representation of a user, responsible for translating
/// Supabase's [supabase.User] into the domain's [AppUser] entity.
///
/// Kept as a plain extension-style factory rather than a Freezed class
/// with its own fields — Supabase's [supabase.User] already carries
/// everything needed, so duplicating its shape here would just be
/// indirection without benefit. This file is the ONLY place in the
/// codebase allowed to reference `supabase.User`.
extension AppUserMapper on supabase.User {
  AppUser toEntity() {
    final metadata = userMetadata ?? const <String, dynamic>{};

    return AppUser(
      id: id,
      email: email ?? '',
      fullName: metadata['full_name'] as String?,
      avatarUrl: metadata['avatar_url'] as String?,
      isEmailVerified: emailConfirmedAt != null,
      createdAt: DateTime.parse(createdAt),
    );
  }
}
