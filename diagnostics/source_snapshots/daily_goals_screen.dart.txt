import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/network/supabase_provider.dart';
import '../../../../shared/widgets/widgets.dart';
import '../../../authentication/application/providers/auth_providers.dart';
import '../../../home/application/providers/home_providers.dart';

class DailyGoalsScreen extends ConsumerStatefulWidget {
  const DailyGoalsScreen({super.key});

  @override
  ConsumerState<DailyGoalsScreen> createState() => _DailyGoalsScreenState();
}

class _DailyGoalsScreenState extends ConsumerState<DailyGoalsScreen> {
  double? _minutes;
  bool _saving = false;

  Future<void> _save() async {
    final user = ref.read(authStateChangesProvider).value;
    if (user == null || _minutes == null) return;

    setState(() => _saving = true);
    try {
      await ref.read(supabaseClientProvider).from('user_home_stats').upsert({
        'user_id': user.id,
        'daily_goal_target_minutes': _minutes!.round(),
      }, onConflict: 'user_id');
      ref.invalidate(homeSummaryProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Daily goal updated')),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not update the goal. Please try again.')),
        );
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final summaryAsync = ref.watch(homeSummaryProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Daily Goal')),
      body: SafeArea(
        top: false,
        child: summaryAsync.when(
          data: (summary) {
            _minutes ??= summary.dailyGoalTargetMinutes.toDouble();
            final minutes = _minutes!;
            return ListView(
              padding: const EdgeInsets.all(AppSpacing.base),
              children: [
                AppCard(
                  child: Column(
                    children: [
                      Icon(Icons.gps_fixed, size: 42, color: Theme.of(context).colorScheme.primary),
                      const SizedBox(height: AppSpacing.md),
                      Text('${minutes.round()} minutes', style: Theme.of(context).textTheme.headlineLarge),
                      const SizedBox(height: AppSpacing.xs),
                      const Text('Choose how much English practice you want to complete each day.'),
                      const SizedBox(height: AppSpacing.lg),
                      Slider(
                        value: minutes,
                        min: 5,
                        max: 60,
                        divisions: 11,
                        label: '${minutes.round()} min',
                        onChanged: (value) => setState(() => _minutes = value),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: AppSpacing.lg),
                ElevatedButton(
                  onPressed: _saving ? null : _save,
                  child: _saving
                      ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Text('Save Daily Goal'),
                ),
              ],
            );
          },
          loading: () => const LoadingWidget(),
          error: (_, __) => ErrorStateWidget(onRetry: () => ref.invalidate(homeSummaryProvider)),
        ),
      ),
    );
  }
}
