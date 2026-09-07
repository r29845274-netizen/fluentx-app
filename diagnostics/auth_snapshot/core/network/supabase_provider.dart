import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

/// Exposes the initialized [SupabaseClient] to the rest of the app.
///
/// `Supabase.initialize()` runs once in `main.dart` before `runApp`,
/// so by the time any widget reads this provider, `Supabase.instance`
/// is already a ready singleton — this provider is just a clean DI
/// seam so datasources depend on a Riverpod provider instead of the
/// global `Supabase.instance` static directly, which keeps them
/// testable (the provider can be overridden with a fake client).
final supabaseClientProvider = Provider<SupabaseClient>((ref) {
  return Supabase.instance.client;
});
