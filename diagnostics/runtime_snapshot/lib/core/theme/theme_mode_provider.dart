import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive_flutter/hive_flutter.dart';

/// Name of the Hive box that stores lightweight app preferences
/// (theme mode, locale, onboarding-seen flag, etc.). Opened once in
/// `main.dart` before `runApp`.
const String kSettingsBoxName = 'settings_box';

const String _kThemeModeKey = 'theme_mode';

/// Persists and exposes the user's selected [ThemeMode].
///
/// Defaults to [ThemeMode.system] on first launch. Reads/writes are
/// synchronous because Hive keeps this small box fully in memory once
/// opened, so there is no loading state to model here.
class ThemeModeNotifier extends Notifier<ThemeMode> {
  late final Box<dynamic> _box;

  @override
  ThemeMode build() {
    _box = Hive.box(kSettingsBoxName);
    final stored = _box.get(_kThemeModeKey) as String?;
    return _decode(stored);
  }

  void setThemeMode(ThemeMode mode) {
    state = mode;
    _box.put(_kThemeModeKey, _encode(mode));
  }

  void toggleLightDark() {
    final next = state == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    setThemeMode(next);
  }

  String _encode(ThemeMode mode) => switch (mode) {
        ThemeMode.light => 'light',
        ThemeMode.dark => 'dark',
        ThemeMode.system => 'system',
      };

  ThemeMode _decode(String? value) => switch (value) {
        'light' => ThemeMode.light,
        'dark' => ThemeMode.dark,
        _ => ThemeMode.system,
      };
}

final themeModeProvider = NotifierProvider<ThemeModeNotifier, ThemeMode>(
  ThemeModeNotifier.new,
);
