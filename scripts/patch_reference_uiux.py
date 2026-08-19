from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')


def patch_text(rel: str, replacements: list[tuple[str, str]]) -> None:
    path = root / rel
    if not path.exists():
        print(f'Skip missing: {rel}')
        return
    text = path.read_text()
    changed = False
    for old, new in replacements:
        if old in text:
            text = text.replace(old, new)
            changed = True
    if changed:
        path.write_text(text)
        print(f'Polished: {rel}')


# IMPORTANT: this patch is deliberately conservative. It only changes
# shared visual tokens/components and simple copy/spacing. It does NOT
# replace complete Dart screens, so existing business logic, providers,
# routing and feature flows stay intact.

patch_text('lib/core/theme/app_theme.dart', [
    ('minimumSize: const Size.fromHeight(54),', 'minimumSize: const Size.fromHeight(56),'),
    ('height: 70,', 'height: 72,'),
    ('indicatorColor: colorScheme.primary.withValues(alpha: 0.14),',
     'indicatorColor: colorScheme.primary.withValues(alpha: 0.16),'),
    ('selectedColor: colorScheme.primary.withValues(alpha: 0.14),',
     'selectedColor: colorScheme.primary.withValues(alpha: 0.16),'),
    ('fontWeight: selected ? FontWeight.w600 : FontWeight.w400,',
     'fontWeight: selected ? FontWeight.w700 : FontWeight.w500,'),
    ('size: 24,', 'size: 25,'),
])

patch_text('lib/core/constants/app_radius.dart', [
    ('static const double sm = 8;', 'static const double sm = 10;'),
    ('static const double md = 16;', 'static const double md = 18;'),
    ('static const double lg = 22;', 'static const double lg = 24;'),
    ('static const double xl = 30;', 'static const double xl = 32;'),
])

patch_text('lib/shared/widgets/cards/app_card.dart', [
    ('scale: _pressed ? 0.98 : 1.0,', 'scale: _pressed ? 0.985 : 1.0,'),
])

patch_text('lib/shared/widgets/buttons/primary_button.dart', [
    ('Icon(icon, size: 20),', 'Icon(icon, size: 19),'),
])

# Home: add a light motivational line without changing providers or actions.
home = root / 'lib/features/home/presentation/screens/home_screen.dart'
if home.exists():
    text = home.read_text()
    marker = "          const SizedBox(height: AppSpacing.lg),\n          DailyGoalCard("
    insert = (
        "          Text(\n"
        "            'Small steps every day build real fluency.',\n"
        "            style: textTheme.bodyMedium?.copyWith(color: colorScheme.onSurfaceVariant),\n"
        "          ),\n"
        "          const SizedBox(height: AppSpacing.lg),\n"
        "          DailyGoalCard("
    )
    if marker in text and 'Small steps every day build real fluency.' not in text:
        home.write_text(text.replace(marker, insert, 1))
        print('Polished: home hero')

# Learn: keep content logic intact, only strengthen page copy where present.
patch_text('lib/features/learn/presentation/screens/learn_hub_screen.dart', [
    ("Text('Learn',", "Text('Learn & Grow',"),
])

# Progress: a clearer learner-facing heading, no chart/provider changes.
patch_text('lib/features/progress/presentation/screens/progress_screen.dart', [
    ("Text('Progress',", "Text('Your Progress',"),
])

# Auth: copy polish only, no form/controller changes.
patch_text('lib/features/authentication/presentation/screens/login_screen.dart', [
    ("'Welcome back'", "'Welcome Back!'") ,
])

# AI Practice: do not replace the screen. Only update heading text if the
# original text is present. This avoids the compile regressions caused by
# the earlier full-screen override.
patch_text('lib/features/ai_practice/presentation/screens/ai_practice_hub_screen.dart', [
    ("'AI Practice'", "'AI English Coach'"),
])

print('Reference-inspired SAFE UI/UX polish applied without replacing feature screens.')
