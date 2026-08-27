import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../theme/theme_mode_provider.dart' show kSettingsBoxName;

const String _kOnboardingCompleteKey = 'onboarding_complete';

/// Whether the user has finished the onboarding flow (goal selection +
/// diagnostic). Persisted in the same `settings_box` Hive box used by
/// [ThemeModeNotifier] since both are small, non-sensitive local flags.
class OnboardingStatusNotifier extends Notifier<bool> {
  late final Box<dynamic> _box;

  @override
  bool build() {
    _box = Hive.box(kSettingsBoxName);
    return _box.get(_kOnboardingCompleteKey, defaultValue: false) as bool;
  }

  void markComplete() {
    state = true;
    _box.put(_kOnboardingCompleteKey, true);
  }

  /// Used by Settings → "Reset onboarding" (QA/debug utility) or
  /// account deletion cleanup.
  void reset() {
    state = false;
    _box.put(_kOnboardingCompleteKey, false);
  }
}

final onboardingCompleteProvider =
    NotifierProvider<OnboardingStatusNotifier, bool>(
  OnboardingStatusNotifier.new,
);
