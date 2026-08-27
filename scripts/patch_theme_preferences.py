from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
provider = root / 'lib/core/theme/theme_mode_provider.dart'
settings = root / 'lib/features/settings/presentation/screens/settings_screen.dart'

if not provider.exists():
    raise SystemExit(f'Theme provider not found: {provider}')

text = provider.read_text(encoding='utf-8')
text = text.replace(
    '/// Defaults to [ThemeMode.system] on first launch.',
    '/// Defaults to [ThemeMode.light] on first launch. The learner can switch to Dark or System in Settings.',
)
text = text.replace(
    "        _ => ThemeMode.system,",
    "        'system' => ThemeMode.system,\n        _ => ThemeMode.light,",
)
provider.write_text(text, encoding='utf-8')

required = [
    "_ => ThemeMode.light,",
    "'system' => ThemeMode.system,",
]
missing = [item for item in required if item not in text]
if missing:
    raise SystemExit('Theme default patch verification failed: ' + ', '.join(missing))

if settings.exists():
    text = settings.read_text(encoding='utf-8')
    text = text.replace(
        "ButtonSegment(value: ThemeMode.system, icon: Icon(Icons.smartphone, size: 16), label: Text('Auto'))",
        "ButtonSegment(value: ThemeMode.system, icon: Icon(Icons.smartphone, size: 16), label: Text('System'))",
    )
    text = text.replace(
        "Text('Appearance', style: textTheme.labelLarge?.copyWith(color: colorScheme.primary)),",
        "Text('Appearance', style: textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),\n            const SizedBox(height: 4),\n            Text('Light is used by default. Change it anytime.', style: textTheme.bodySmall?.copyWith(color: colorScheme.onSurfaceVariant)),",
    )
    settings.write_text(text, encoding='utf-8')

print('Theme preference fixed: first launch Light; user can choose Light, Dark or System in Settings.')
