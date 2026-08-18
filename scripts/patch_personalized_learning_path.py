from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')
path = root / 'lib/features/learn/presentation/screens/learn_hub_screen.dart'
if not path.exists():
    raise SystemExit(f'Learn hub screen not found: {path}')

code = r'''import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:supabase_flutter/supabase_flutter.dart' as supabase;

import '../../../../core/constants/app_spacing.dart';
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
  List<Map<String, dynamic>> _weeks = const [];
  Map<String, dynamic> _profile = const {};
  String _filter = 'ALL';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final state = await _client.rpc('get_my_onboarding_state');
      final path = await _client.rpc('get_my_learning_path');
      Map<String, dynamic> profile = const {};
      if (state is List && state.isNotEmpty) {
        profile = Map<String, dynamic>.from(state.first as Map);
      } else if (state is Map) {
        profile = Map<String, dynamic>.from(state);
      }
      final rows = path is List
          ? path.map((e) => Map<String, dynamic>.from(e as Map)).toList()
          : <Map<String, dynamic>>[];
      if (!mounted) return;
      setState(() {
        _profile = profile;
        _weeks = rows;
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

  int get _currentWeek => int.tryParse((_profile['current_week'] ?? 1).toString()) ?? 1;
  String get _currentLevel => (_profile['current_cefr_level'] ?? 'A1').toString();
  String get _audience => (_profile['audience_type'] ?? 'general_learner').toString();
  String get _goal => (_profile['learning_goal'] ?? 'general_fluency').toString();

  String _pretty(String value) => value
      .split('_')
      .where((e) => e.isNotEmpty)
      .map((e) => '${e[0].toUpperCase()}${e.substring(1)}')
      .join(' ');

  int _masteredCount() => _weeks.where((w) => w['progress_status'] == 'mastered').length;

  List<Map<String, dynamic>> get _visibleWeeks {
    if (_filter == 'ALL') return _weeks;
    return _weeks.where((w) => (w['cefr_level'] ?? '').toString() == _filter).toList();
  }

  Map<String, dynamic>? get _currentWeekData {
    for (final week in _weeks) {
      if ((week['week_number'] as num?)?.toInt() == _currentWeek) return week;
    }
    return null;
  }

  void _openWeek(Map<String, dynamic> week) {
    final status = (week['progress_status'] ?? 'locked').toString();
    final weekNo = (week['week_number'] as num?)?.toInt() ?? 1;
    final locked = status == 'locked';
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) {
        final colors = Theme.of(context).colorScheme;
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(AppSpacing.base, 0, AppSpacing.base, AppSpacing.lg),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(children: [
                  _LevelBadge(level: (week['cefr_level'] ?? 'A1').toString()),
                  const SizedBox(width: 8),
                  Text('Week $weekNo', style: Theme.of(context).textTheme.labelLarge),
                  const Spacer(),
                  _StatusPill(status: status),
                ]),
                const SizedBox(height: AppSpacing.md),
                Text((week['title'] ?? 'Personalized English').toString(), style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
                const SizedBox(height: AppSpacing.xs),
                Text((week['focus'] ?? '').toString(), style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: colors.onSurfaceVariant)),
                const SizedBox(height: AppSpacing.lg),
                Row(children: [
                  Expanded(child: _MiniMetric(icon: Icons.verified_outlined, label: 'Pass', value: '${week['pass_score'] ?? 70}%')),
                  const SizedBox(width: 10),
                  Expanded(child: _MiniMetric(icon: Icons.mic_none_rounded, label: 'Speaking', value: '${week['speaking_min_score'] ?? 60}%')),
                ]),
                const SizedBox(height: AppSpacing.lg),
                Text('This week includes', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
                const SizedBox(height: AppSpacing.sm),
                const Wrap(spacing: 8, runSpacing: 8, children: [
                  _ModuleChip(icon: Icons.translate_rounded, label: 'Vocabulary'),
                  _ModuleChip(icon: Icons.menu_book_outlined, label: 'Grammar'),
                  _ModuleChip(icon: Icons.headphones_rounded, label: 'Listening'),
                  _ModuleChip(icon: Icons.mic_rounded, label: 'Speaking'),
                  _ModuleChip(icon: Icons.work_outline_rounded, label: 'Real-life Practice'),
                ]),
                const SizedBox(height: AppSpacing.lg),
                if (locked)
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(AppSpacing.base),
                    decoration: BoxDecoration(color: colors.surfaceContainerHighest, borderRadius: BorderRadius.circular(18)),
                    child: Row(children: [
                      Icon(Icons.lock_outline_rounded, color: colors.onSurfaceVariant),
                      const SizedBox(width: 10),
                      Expanded(child: Text('Complete the previous week mastery requirement to unlock this week.', style: TextStyle(color: colors.onSurfaceVariant))),
                    ]),
                  )
                else
                  PrimaryButton(label: status == 'mastered' ? 'Review This Week' : 'Start Week $weekNo', onPressed: () {
                    Navigator.of(context).pop();
                    context.push('/vocabulary');
                  }),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return ErrorStateWidget(message: _error!, onRetry: _load);
    }
    if (_weeks.isEmpty) {
      return const EmptyStateWidget(
        icon: Icons.route_outlined,
        title: 'Your path is being prepared',
        message: 'Complete onboarding and placement to generate your personalized course.',
      );
    }

    final current = _currentWeekData ?? _weeks.first;
    final position = (_currentWeek / 60).clamp(0.0, 1.0);
    return RefreshIndicator(
      onRefresh: _load,
      child: CustomScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(AppSpacing.base, AppSpacing.base, AppSpacing.base, 0),
            sliver: SliverToBoxAdapter(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('Your Learning Path', style: Theme.of(context).textTheme.displaySmall?.copyWith(fontWeight: FontWeight.w900)),
                const SizedBox(height: 6),
                Text('${_pretty(_audience)} • ${_pretty(_goal)}', style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: colors.onSurfaceVariant)),
                const SizedBox(height: AppSpacing.base),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(AppSpacing.lg),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(colors: [colors.primary, colors.secondary]),
                    borderRadius: BorderRadius.circular(26),
                    boxShadow: [BoxShadow(color: colors.primary.withValues(alpha: .18), blurRadius: 28, offset: const Offset(0, 12))],
                  ),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Row(children: [
                      Container(
                        width: 54,
                        height: 54,
                        alignment: Alignment.center,
                        decoration: BoxDecoration(color: colors.onPrimary.withValues(alpha: .16), borderRadius: BorderRadius.circular(16)),
                        child: Text(_currentLevel, style: Theme.of(context).textTheme.titleLarge?.copyWith(color: colors.onPrimary, fontWeight: FontWeight.w900)),
                      ),
                      const SizedBox(width: 12),
                      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text('Continue your journey', style: Theme.of(context).textTheme.labelLarge?.copyWith(color: colors.onPrimary.withValues(alpha: .82))),
                        const SizedBox(height: 3),
                        Text('Week $_currentWeek • ${current['title'] ?? 'Personalized English'}', maxLines: 2, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.titleLarge?.copyWith(color: colors.onPrimary, fontWeight: FontWeight.w900)),
                      ])),
                    ]),
                    const SizedBox(height: AppSpacing.base),
                    ClipRRect(borderRadius: BorderRadius.circular(99), child: LinearProgressIndicator(value: position, minHeight: 8, backgroundColor: colors.onPrimary.withValues(alpha: .22), valueColor: AlwaysStoppedAnimation(colors.onPrimary))),
                    const SizedBox(height: 8),
                    Row(children: [
                      Text('Path position: $_currentWeek/60', style: TextStyle(color: colors.onPrimary.withValues(alpha: .86))),
                      const Spacer(),
                      Text('${_masteredCount()} mastered', style: TextStyle(color: colors.onPrimary, fontWeight: FontWeight.w800)),
                    ]),
                    const SizedBox(height: AppSpacing.base),
                    SizedBox(width: double.infinity, child: FilledButton.tonal(onPressed: () => _openWeek(current), child: const Text('Continue Learning'))),
                  ]),
                ),
                const SizedBox(height: AppSpacing.lg),
                Row(children: [
                  Text('60-Week Roadmap', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
                  const Spacer(),
                  Text('A1 → C1', style: Theme.of(context).textTheme.labelLarge?.copyWith(color: colors.primary, fontWeight: FontWeight.w900)),
                ]),
                const SizedBox(height: AppSpacing.sm),
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(children: ['ALL', 'A1', 'A2', 'B1', 'B2', 'C1'].map((level) {
                    final selected = _filter == level;
                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ChoiceChip(label: Text(level == 'ALL' ? 'All Levels' : level), selected: selected, onSelected: (_) => setState(() => _filter = level)),
                    );
                  }).toList()),
                ),
                const SizedBox(height: AppSpacing.base),
              ]),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(AppSpacing.base, 0, AppSpacing.base, AppSpacing.xxl),
            sliver: SliverList.separated(
              itemCount: _visibleWeeks.length,
              separatorBuilder: (_, __) => const SizedBox(height: AppSpacing.sm),
              itemBuilder: (context, index) {
                final week = _visibleWeeks[index];
                final weekNo = (week['week_number'] as num?)?.toInt() ?? 1;
                final status = (week['progress_status'] ?? 'locked').toString();
                final isCurrent = weekNo == _currentWeek;
                final checkpoint = week['is_checkpoint'] == true;
                return _WeekCard(
                  weekNumber: weekNo,
                  level: (week['cefr_level'] ?? 'A1').toString(),
                  title: (week['title'] ?? 'Personalized English').toString(),
                  focus: (week['focus'] ?? '').toString(),
                  status: status,
                  current: isCurrent,
                  checkpoint: checkpoint,
                  onTap: () => _openWeek(week),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _WeekCard extends StatelessWidget {
  const _WeekCard({required this.weekNumber, required this.level, required this.title, required this.focus, required this.status, required this.current, required this.checkpoint, required this.onTap});
  final int weekNumber;
  final String level;
  final String title;
  final String focus;
  final String status;
  final bool current;
  final bool checkpoint;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final locked = status == 'locked';
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(20),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.all(AppSpacing.base),
        decoration: BoxDecoration(
          color: current ? colors.primaryContainer.withValues(alpha: .55) : colors.surface,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: current ? colors.primary : colors.outlineVariant, width: current ? 2 : 1),
          boxShadow: current ? [BoxShadow(color: colors.primary.withValues(alpha: .09), blurRadius: 20, offset: const Offset(0, 8))] : null,
        ),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(
            width: 50,
            height: 50,
            alignment: Alignment.center,
            decoration: BoxDecoration(color: locked ? colors.surfaceContainerHighest : colors.primaryContainer, borderRadius: BorderRadius.circular(15)),
            child: locked ? Icon(Icons.lock_outline_rounded, color: colors.onSurfaceVariant) : Text('$weekNumber', style: TextStyle(color: colors.primary, fontWeight: FontWeight.w900, fontSize: 17)),
          ),
          const SizedBox(width: 12),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              _LevelBadge(level: level),
              if (checkpoint) ...[
                const SizedBox(width: 7),
                const _CheckpointBadge(),
              ],
              const Spacer(),
              _StatusPill(status: status),
            ]),
            const SizedBox(height: 8),
            Text(title, maxLines: 2, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900, color: locked ? colors.onSurfaceVariant : colors.onSurface)),
            if (focus.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(focus, maxLines: 2, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: colors.onSurfaceVariant)),
            ],
          ])),
        ]),
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
      decoration: BoxDecoration(color: colors.primaryContainer, borderRadius: BorderRadius.circular(999)),
      child: Text(level, style: Theme.of(context).textTheme.labelSmall?.copyWith(color: colors.primary, fontWeight: FontWeight.w900)),
    );
  }
}

class _CheckpointBadge extends StatelessWidget {
  const _CheckpointBadge();
  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
      decoration: BoxDecoration(color: colors.tertiaryContainer, borderRadius: BorderRadius.circular(999)),
      child: Text('CHECKPOINT', style: Theme.of(context).textTheme.labelSmall?.copyWith(color: colors.onTertiaryContainer, fontWeight: FontWeight.w900)),
    );
  }
}

class _StatusPill extends StatelessWidget {
  const _StatusPill({required this.status});
  final String status;
  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final (label, icon) = switch (status) {
      'mastered' => ('Mastered', Icons.check_circle_rounded),
      'in_progress' => ('In progress', Icons.play_circle_fill_rounded),
      'remediation' => ('Practice', Icons.refresh_rounded),
      'available' => ('Ready', Icons.play_arrow_rounded),
      'placed' => ('Placed', Icons.fast_forward_rounded),
      _ => ('Locked', Icons.lock_outline_rounded),
    };
    final active = status != 'locked';
    return Row(mainAxisSize: MainAxisSize.min, children: [
      Icon(icon, size: 15, color: active ? colors.primary : colors.onSurfaceVariant),
      const SizedBox(width: 4),
      Text(label, style: Theme.of(context).textTheme.labelSmall?.copyWith(color: active ? colors.primary : colors.onSurfaceVariant, fontWeight: FontWeight.w800)),
    ]);
  }
}

class _MiniMetric extends StatelessWidget {
  const _MiniMetric({required this.icon, required this.label, required this.value});
  final IconData icon;
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: colors.surfaceContainerHighest, borderRadius: BorderRadius.circular(16)),
      child: Row(children: [
        Icon(icon, color: colors.primary),
        const SizedBox(width: 8),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(label, style: Theme.of(context).textTheme.labelSmall?.copyWith(color: colors.onSurfaceVariant)),
          Text(value, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
        ])),
      ]),
    );
  }
}

class _ModuleChip extends StatelessWidget {
  const _ModuleChip({required this.icon, required this.label});
  final IconData icon;
  final String label;
  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 8),
      decoration: BoxDecoration(color: colors.surfaceContainerHighest, borderRadius: BorderRadius.circular(999)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 17, color: colors.primary),
        const SizedBox(width: 6),
        Text(label, style: Theme.of(context).textTheme.labelMedium?.copyWith(fontWeight: FontWeight.w700)),
      ]),
    );
  }
}
'''

path.write_text(code)
print('Personalized 60-week learning path UI applied.')
