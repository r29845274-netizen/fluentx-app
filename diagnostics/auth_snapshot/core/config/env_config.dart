/// Environment configuration, injected at build time via
/// `--dart-define`. Never hardcode API keys/URLs directly in source.
///
/// Example run command per flavor:
/// ```bash
/// flutter run \
///   --dart-define=SUPABASE_URL=https://xxxx.supabase.co \
///   --dart-define=SUPABASE_ANON_KEY=your-anon-key \
///   --dart-define=FLAVOR=dev
/// ```
///
/// For CI/CD (Codemagic), these are injected as encrypted environment
/// variables per build flavor (dev/staging/prod) rather than committed
/// to the repo.
abstract final class EnvConfig {
  /// Public RevenueCat Android SDK key. Supply at build time:
  /// --dart-define=REVENUECAT_ANDROID_API_KEY=goog_...
  static const revenueCatAndroidApiKey = String.fromEnvironment(
    'REVENUECAT_ANDROID_API_KEY',
    defaultValue: '',
  );

  const EnvConfig._();

  static const String supabaseUrl = String.fromEnvironment(
    'SUPABASE_URL',
    defaultValue: 'https://ampcghxowbeocfqqnnvk.supabase.co',
  );
  static const String supabaseAnonKey = String.fromEnvironment(
    'SUPABASE_ANON_KEY',
    defaultValue: 'sb_publishable_TF58ThseSYp-CERYJklnbA_PL_F_rGo',
  );
  static const String revenueCatApiKey = String.fromEnvironment('REVENUECAT_API_KEY');
  static const String flavor = String.fromEnvironment('FLAVOR', defaultValue: 'dev');

  static bool get isConfigured => supabaseUrl.isNotEmpty && supabaseAnonKey.isNotEmpty;
}
