from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')

# Resolve the screen defensively. The source archive has used this path historically,
# but the fallback keeps CI resilient if the feature is moved later.
candidates = list(root.rglob('learn_hub_screen.dart'))
if not candidates:
    for dart_file in root.rglob('*.dart'):
        try:
            if 'class LearnHubScreen' in dart_file.read_text(errors='ignore'):
                candidates.append(dart_file)
                break
        except OSError:
            pass

if not candidates:
    raise SystemExit('Could not locate LearnHubScreen in extracted Flutter source')

path = candidates[0]
print(f'Patching learning path screen: {path}')

code = r'''import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:supabase_flutter/supabase_flutter.dart' as supabase;

import '../../../../core/constants/app_spacing.dart';
import '../../../../routes/route_paths.dart';
import '../../../../shared/widgets/widgets.dart';

class LearnHubScreen extends StatefulWidget {
  const LearnHubScreen({super.key});

  @override
  State<LearnHubScreen> createState() => _LearnHubScreenState();
}

class _LearnHubScreenState extends State<LearnHubScreen> {
  final _client = supabase.Supabase.instance.client;

  bool _loading = true;
  String? _error;
  Map<String, dynamic> _profile = <String, dynamic>{};
  List<Map<String, dynamic>> _weeks = <Map<String, dynamic>>[];
  String _levelFilter = 'ALL';

  @override
  void initState() {
    super.initState();
    _loadPath();
  }

  Future<void> _loadPath() async {
    if (mounted) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }

    try {
      final stateResponse = await _client.rpc('get_my_onboarding_state');
      final pathResponse = await _client.rpc('get_my_learning_path');

      final profile = stateResponse is Map
          ? Map<String, dynamic>.from(stateResponse)
          : <String, dynamic>{};

      final weeks = pathResponse is List
          ? pathResponse
              .whereType<Map>()
              .map((row) => Map<String, dynamic>.from(row))
              .toList()
          : <Map<String, dynamic>>[];

      if (!mounted) return;
      setState(() {
        _profile = profile;
        _weeks = weeks;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = 'Could not load your personalized learning path.';
      });
    }
  }

  int get _currentWeek =>
      int.tryParse((_profile['current_week'] ?? 1).toString()) ?? 1;

  String get _currentLevel =>
      (_profile['current_cefr_level'] ?? 'A1').toString();

  String get _audience =>
      (_profile['audience_type'] ?? 'general_learner').toString();

  String get _goal =>
      (_profile['learning_goal'] ?? 'general_fluency').toString();

  String _pretty(String value) {
    return value
        .split('_')
        .where((part) => part.isNotEmpty)
        .map((part) => '${part[0].toUpperCase()}${part.substring(1)}')
        .join(' ');
  }

  List<Map<String, dynamic>> get _visibleWeeks {
    if (_levelFilter == 'ALL') return _weeks;
    return _weeks
        .where((week) => week['cefr_level']?.toString() == _levelFilter)
        .toList();
  }

  Map<String, dynamic>? get _currentWeekData {
    for (final week in _weeks) {
      final number = int.tryParse((week['week_number'] ?? '').toString());
      if (number == _currentWeek) return week;
    }
    return _weeks.isEmpty ? null : _weeks.first;
  }

  int get _masteredCount =>
      _weeks.where((week) => week['progress_status'] == 'mastered').length;

  bool _isLocked(Map<String, dynamic> week) {
    return (week['progress_status'] ?? 'locked').toString() == 'locked';
  }

  void _openWeek(Map<String, dynamic> week) {
    final weekNumber =
        int.tryParse((week['week_number'] ?? 1).toString()) ?? 1;
    if (_isLocked(week)) {
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(
          const SnackBar(
            content: Text('Complete your current week mastery test to unlock this week.'),
          ),
        );
      return;
    }

    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (sheetContext) {
        final colors = Theme.of(sheetContext).colorScheme;
        final level = (week['cefr_level'] ?? 'A1').toString();
        final title = (week['title'] ?? 'Personalized English').toString();
        final focus = (week['focus'] ?? '').toString();
        final status = (week['progress_status'] ?? 'available').toString();
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(
              AppSpacing.base,
              0,
              AppSpacing.base,
              AppSpacing.lg,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    _LevelBadge(level: level),
                    const SizedBox(width: AppSpacing.sm),
                    Text(
                      'Week $weekNumber',
                      style: Theme.of(sheetContext).textTheme.labelLarge,
                    ),
                    const Spacer(),
                    _StatusLabel(status: status),
                  ],
                ),
                const SizedBox(height: AppSpacing.md),
                Text(
                  title,
                  style: Theme.of(sheetContext).textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                if (focus.isNotEmpty) ...[
                  const SizedBox(height: AppSpacing.sm),
                  Text(
                    focus,
                    style: Theme.of(sheetContext).textTheme.bodyMedium?.copyWith(
                          color: colors.onSurfaceVariant,
                        ),
                  ),
                ],
                const SizedBox(height: AppSpacing.lg),
                Row(
                  children: [
                    Expanded(
                      child: _MetricBox(
                        icon: Icons.verified_outlined,
                        label: 'Pass score',
                        value: '${week['pass_score'] ?? 70}%',
                      ),
                    ),
                    const SizedBox(width: AppSpacing.sm),
                    Expanded(
                      child: _MetricBox(
                        icon: Icons.mic_none_rounded,
                        label: 'Speaking',
                        value: '${week['speaking_min_score'] ?? 60}%',
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.lg),
                PrimaryButton(
                  label: status == 'mastered'
                      ? 'Review Week $weekNumber'
                      : 'Start Week $weekNumber',
                  onPressed: () {
                    Navigator.of(sheetContext).pop();
                    context.push(RoutePaths.vocabulary);
                  },
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        body: SafeArea(child: Center(child: CircularProgressIndicator())),
      );
    }

    if (_error != null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Learn')),
        body: ErrorStateWidget(
          message: _error!,
          onRetry: _loadPath,
        ),
      );
    }

    if (_weeks.isEmpty) {
      return Scaffold(
        appBar: AppBar(title: const Text('Learn')),
        body: const EmptyStateWidget(
          icon: Icons.route_outlined,
          title: 'Your learning path is being prepared',
          message: 'Complete onboarding and your level check to generate your personalized course.',
        ),
      );
    }

    final colors = Theme.of(context).colorScheme;
    final current = _currentWeekData ?? _weeks.first;
    final progress = (_currentWeek / 60.0).clamp(0.0, 1.0).toDouble();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Learn'),
        actions: [
          IconButton(
            tooltip: 'Refresh learning path',
            onPressed: _loadPath,
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadPath,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(
            AppSpacing.base,
            AppSpacing.sm,
            AppSpacing.base,
            AppSpacing.xxl,
          ),
          children: [
            Text(
              'Your Learning Path',
              style: Theme.of(context).textTheme.displaySmall?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
            ),
            const SizedBox(height: AppSpacing.xs),
            Text(
              '${_pretty(_audience)} • ${_pretty(_goal)}',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: colors.onSurfaceVariant,
                  ),
            ),
            const SizedBox(height: AppSpacing.base),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(AppSpacing.lg),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [colors.primary, colors.secondary],
                ),
                borderRadius: BorderRadius.circular(26),
                boxShadow: [
                  BoxShadow(
                    color: colors.primary.withValues(alpha: 0.16),
                    blurRadius: 24,
                    offset: const Offset(0, 10),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 56,
                        height: 56,
                        alignment: Alignment.center,
                        decoration: BoxDecoration(
                          color: colors.onPrimary.withValues(alpha: 0.16),
                          borderRadius: BorderRadius.circular(18),
                        ),
                        child: Text(
                          _currentLevel,
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                color: colors.onPrimary,
                                fontWeight: FontWeight.w900,
                              ),
                        ),
                      ),
                      const SizedBox(width: AppSpacing.md),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Continue your journey',
                              style: Theme.of(context).textTheme.labelLarge?.copyWith(
                                    color: colors.onPrimary.withValues(alpha: 0.84),
                                  ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Week $_currentWeek • ${current['title'] ?? 'Personalized English'}',
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                    color: colors.onPrimary,
                                    fontWeight: FontWeight.w800,
                                  ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.base),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(99),
                    child: LinearProgressIndicator(
                      value: progress,
                      minHeight: 8,
                      backgroundColor: colors.onPrimary.withValues(alpha: 0.22),
                      valueColor: AlwaysStoppedAnimation<Color>(colors.onPrimary),
                    ),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  Row(
                    children: [
                      Text(
                        'Week $_currentWeek of 60',
                        style: TextStyle(
                          color: colors.onPrimary.withValues(alpha: 0.88),
                        ),
                      ),
                      const Spacer(),
                      Text(
                        '$_masteredCount mastered',
                        style: TextStyle(
                          color: colors.onPrimary,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.base),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.tonal(
                      onPressed: () => _openWeek(current),
                      child: const Text('Continue Learning'),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.lg),
            Text(
              'Quick Practice',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
            ),
            const SizedBox(height: AppSpacing.sm),
            Row(
              children: [
                Expanded(
                  child: _QuickModule(
                    icon: Icons.menu_book_outlined,
                    label: 'Vocabulary',
                    onTap: () => context.push(RoutePaths.vocabulary),
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: _QuickModule(
                    icon: Icons.spellcheck_rounded,
                    label: 'Grammar',
                    onTap: () => context.push(RoutePaths.grammar),
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: _QuickModule(
                    icon: Icons.headphones_rounded,
                    label: 'Listening',
                    onTap: () => context.push(RoutePaths.listening),
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.lg),
            Row(
              children: [
                Text(
                  '60-Week Roadmap',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const Spacer(),
                Text(
                  'A1 → C1',
                  style: Theme.of(context).textTheme.labelLarge?.copyWith(
                        color: colors.primary,
                        fontWeight: FontWeight.w800,
                      ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.sm),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: ['ALL', 'A1', 'A2', 'B1', 'B2', 'C1']
                    .map(
                      (level) => Padding(
                        padding: const EdgeInsets.only(right: AppSpacing.sm),
                        child: ChoiceChip(
                          label: Text(level == 'ALL' ? 'All Levels' : level),
                          selected: _levelFilter == level,
                          onSelected: (_) {
                            setState(() => _levelFilter = level);
                          },
                        ),
                      ),
                    )
                    .toList(),
              ),
            ),
            const SizedBox(height: AppSpacing.base),
            ..._visibleWeeks.map(
              (week) => Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                child: _WeekCard(
                  week: week,
                  currentWeek: _currentWeek,
                  onTap: () => _openWeek(week),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _QuickModule extends StatelessWidget {
  const _QuickModule({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(18),
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.sm,
          vertical: AppSpacing.base,
        ),
        decoration: BoxDecoration(
          color: colors.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(18),
        ),
        child: Column(
          children: [
            Icon(icon, color: colors.primary),
            const SizedBox(height: AppSpacing.sm),
            Text(
              label,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.labelMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}

class _WeekCard extends StatelessWidget {
  const _WeekCard({
    required this.week,
    required this.currentWeek,
    required this.onTap,
  });

  final Map<String, dynamic> week;
  final int currentWeek;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final weekNumber =
        int.tryParse((week['week_number'] ?? 1).toString()) ?? 1;
    final status = (week['progress_status'] ?? 'locked').toString();
    final level = (week['cefr_level'] ?? 'A1').toString();
    final title = (week['title'] ?? 'Personalized English').toString();
    final focus = (week['focus'] ?? '').toString();
    final locked = status == 'locked';
    final current = weekNumber == currentWeek;
    final checkpoint = week['is_checkpoint'] == true;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(20),
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.base),
        decoration: BoxDecoration(
          color: current
              ? colors.primaryContainer.withValues(alpha: 0.55)
              : colors.surface,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: current ? colors.primary : colors.outlineVariant,
            width: current ? 2 : 1,
          ),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 50,
              height: 50,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: locked
                    ? colors.surfaceContainerHighest
                    : colors.primaryContainer,
                borderRadius: BorderRadius.circular(15),
              ),
              child: locked
                  ? Icon(
                      Icons.lock_outline_rounded,
                      color: colors.onSurfaceVariant,
                    )
                  : Text(
                      '$weekNumber',
                      style: TextStyle(
                        color: colors.primary,
                        fontWeight: FontWeight.w900,
                        fontSize: 17,
                      ),
                    ),
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      _LevelBadge(level: level),
                      if (checkpoint) ...[
                        const SizedBox(width: AppSpacing.sm),
                        Icon(
                          Icons.flag_outlined,
                          size: 17,
                          color: colors.tertiary,
                        ),
                      ],
                      const Spacer(),
                      _StatusLabel(status: status),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  Text(
                    title,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w800,
                          color: locked
                              ? colors.onSurfaceVariant
                              : colors.onSurface,
                        ),
                  ),
                  if (focus.isNotEmpty) ...[
                    const SizedBox(height: AppSpacing.xs),
                    Text(
                      focus,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: colors.onSurfaceVariant,
                          ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _LevelBadge extends StatelessWidget {
  const _LevelBadge({required this.level});
  final String level;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: colors.primaryContainer,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        level,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: colors.primary,
              fontWeight: FontWeight.w800,
            ),
      ),
    );
  }
}

class _StatusLabel extends StatelessWidget {
  const _StatusLabel({required this.status});
  final String status;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    String label = 'Locked';
    IconData icon = Icons.lock_outline_rounded;

    if (status == 'mastered') {
      label = 'Mastered';
      icon = Icons.check_circle_outline_rounded;
    } else if (status == 'in_progress') {
      label = 'In progress';
      icon = Icons.play_circle_outline_rounded;
    } else if (status == 'remediation') {
      label = 'Practice';
      icon = Icons.refresh_rounded;
    } else if (status == 'available') {
      label = 'Ready';
      icon = Icons.play_arrow_rounded;
    } else if (status == 'placed') {
      label = 'Placed';
      icon = Icons.fast_forward_rounded;
    }

    final active = status != 'locked';
    final color = active ? colors.primary : colors.onSurfaceVariant;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 15, color: color),
        const SizedBox(width: 4),
        Text(
          label,
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: color,
                fontWeight: FontWeight.w700,
              ),
        ),
      ],
    );
  }
}

class _MetricBox extends StatelessWidget {
  const _MetricBox({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: colors.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          Icon(icon, color: colors.primary),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: colors.onSurfaceVariant,
                      ),
                ),
                Text(
                  value,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
'''

path.write_text(code, encoding='utf-8')
print('Safe personalized 60-week learning path UI applied.')
