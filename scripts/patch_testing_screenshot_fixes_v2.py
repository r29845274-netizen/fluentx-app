from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'fluentx_admin_secure')


def patch(path_rel: str, transform):
    path = root / path_rel
    if not path.exists():
        raise SystemExit(f'Missing target: {path_rel}')
    old = path.read_text(encoding='utf-8')
    new = transform(old)
    if new == old:
        print(f'No change needed: {path_rel}')
        return
    path.write_text(new, encoding='utf-8')
    print(f'Updated: {path_rel}')


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    s = text.find(start)
    if s < 0:
        if replacement.strip() in text:
            return text
        raise SystemExit(f'{label}: start marker not found')
    e = text.find(end, s)
    if e < 0:
        raise SystemExit(f'{label}: end marker not found')
    return text[:s] + replacement + text[e:]


# ---------------------------------------------------------------------------
# Maya: truthful offline status, more useful local replies and a fully
# scrollable/responsive voice screen so narrow devices cannot RenderFlex
# overflow. This directly fixes the 47px overflow seen in device QA.
# ---------------------------------------------------------------------------
def fix_maya(text: str) -> str:
    local_marker = "  bool _isLocalScenario(Map<String, dynamic> scenario) => scenario['id'] == 'local-free-talk';\n"
    offline_getter = "\n  bool get _offlineSession => _sessionId?.startsWith('local-') == true;\n"
    if '_offlineSession =>' not in text:
        if local_marker not in text:
            raise SystemExit('Maya local scenario marker not found')
        text = text.replace(local_marker, local_marker + offline_getter, 1)

    local_reply = r'''  String _localPracticeReply(String message) {
    final clean = message.trim();
    final lower = clean.toLowerCase();
    final words = clean.split(RegExp(r'\s+')).where((w) => w.isNotEmpty).length;

    if (lower == 'hi' || lower == 'hii' || lower == 'hlo' ||
        lower == 'hello' || lower == 'hey') {
      return 'Guided offline coach: A natural start is “Hi Maya, how are you today?” Say it once, then add how your day is going.';
    }
    if (lower.contains("what's up") || lower.contains('whats up') ||
        lower.contains('what s up') || lower.contains('what’s up')) {
      return 'Guided offline coach: “What’s up?” is natural casual English. Try: “What’s up, Maya? How’s your day going?”';
    }
    if (words < 5) {
      return 'Guided offline coach: Good start. Turn it into one complete sentence, then add one reason or example.';
    }
    if (clean.endsWith('?')) {
      return 'Guided offline coach: Nice question. Now answer it yourself in two complete English sentences and add one detail.';
    }
    return 'Guided offline coach: Good sentence. Make it stronger by adding why, when, where, or how, then say the full idea naturally.';
  }

'''
    text = replace_between(
        text,
        '  String _localPracticeReply(String message) {',
        '  int _limitForTier(String tier)',
        local_reply,
        'Maya local reply',
    )

    online_header_old = r'''            const Row(children: [
              Text('Maya', style: TextStyle(fontWeight: FontWeight.w900)),
              SizedBox(width: 5),
              Icon(Icons.circle, size: 8, color: Colors.green),
            ]),
            Text(free ? 'Online · Free Talk' : 'Online · ${(_active?['title'] ?? '').toString()}',
                maxLines: 1, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.labelSmall),
'''
    online_header_new = r'''            Row(children: [
              const Text('Maya', style: TextStyle(fontWeight: FontWeight.w900)),
              const SizedBox(width: 5),
              Icon(
                Icons.circle,
                size: 8,
                color: _offlineSession ? Colors.orange : Colors.green,
              ),
            ]),
            Text(
              _offlineSession
                  ? 'Guided Offline · Free Talk'
                  : free
                      ? 'Online · Free Talk'
                      : 'Online · ${(_active?['title'] ?? '').toString()}',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.labelSmall,
            ),
'''
    if online_header_old in text:
        text = text.replace(online_header_old, online_header_new, 1)
    elif 'Guided Offline · Free Talk' not in text:
        raise SystemExit('Maya online status marker not found')

    catch_old = r'''    } catch (e) {
      if (!mounted) return;
      final raw = e.toString().toLowerCase();
      setState(() {
        _error = raw.contains('limit') || raw.contains('daily_ai_limit_reached')
            ? 'Your AI Conversation time for today is complete. It resets daily.'
            : 'Maya could not reply right now. Please try again.';
        _sending = false;
      });
    }
'''
    catch_new = r'''    } catch (e) {
      if (!mounted) return;
      final raw = e.toString().toLowerCase();
      if (raw.contains('limit') || raw.contains('daily_ai_limit_reached')) {
        setState(() {
          _error = 'Your AI Conversation time for today is complete. It resets daily.';
          _sending = false;
        });
        return;
      }

      final fallbackReply = _localPracticeReply(clean);
      setState(() {
        _sessionId = 'local-${DateTime.now().millisecondsSinceEpoch}';
        _active = _localFreeTalkScenario();
        _turns.add(_Turn('assistant', fallbackReply));
        _error = 'AI service is reconnecting. Guided offline practice is active.';
        _sending = false;
      });
      _scrollDown();
      if (_speakerOn) await _speak(fallbackReply, 'en-IN', 'encouraging');
    }
'''
    if catch_old in text:
        text = text.replace(catch_old, catch_new, 1)
    elif 'Guided offline practice is active.' not in text:
        raise SystemExit('Maya reply failure marker not found')

    voice_func = r'''  Widget _voiceView() {
    final offline = _offlineSession;
    final statusColor = offline ? Colors.orange : Colors.green;

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          tooltip: 'Back to text conversation',
          icon: const Icon(Icons.arrow_back_rounded),
          onPressed: _leaveVoiceMode,
        ),
        title: const Column(children: [
          Text('Voice Conversation', style: TextStyle(fontWeight: FontWeight.w900)),
          Text('Talk with Maya', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w400)),
        ]),
        actions: [
          IconButton(
            tooltip: 'End conversation',
            onPressed: _closeConversation,
            icon: const Icon(Icons.close_rounded),
          ),
        ],
      ),
      body: SafeArea(
        top: false,
        child: LayoutBuilder(
          builder: (context, constraints) {
            final compact = constraints.maxHeight < 700 || constraints.maxWidth < 380;
            final avatarSize = compact ? 104.0 : 126.0;
            final micSize = compact ? 86.0 : 100.0;
            final titleStyle = compact
                ? Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)
                : Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900);

            return SingleChildScrollView(
              padding: EdgeInsets.fromLTRB(14, compact ? 10 : 14, 14, 22),
              child: ConstrainedBox(
                constraints: BoxConstraints(minHeight: (constraints.maxHeight - 32).clamp(0, double.infinity)),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
                      decoration: BoxDecoration(
                        color: statusColor.withValues(alpha: .12),
                        borderRadius: BorderRadius.circular(99),
                      ),
                      child: Row(mainAxisSize: MainAxisSize.min, children: [
                        Icon(Icons.graphic_eq_rounded, color: statusColor, size: 18),
                        const SizedBox(width: 6),
                        Flexible(
                          child: Text(
                            offline
                                ? 'Guided Offline Mode'
                                : _voicePaused
                                    ? 'Voice Mode Paused'
                                    : 'Voice Mode Active',
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(fontWeight: FontWeight.w800, color: statusColor),
                          ),
                        ),
                      ]),
                    ),
                    SizedBox(height: compact ? 10 : 16),
                    _voiceWave(),
                    SizedBox(height: compact ? 8 : 14),
                    _MayaAvatar(size: avatarSize, expression: _expression),
                    SizedBox(height: compact ? 10 : 16),
                    Text(
                      _voicePaused
                          ? 'Voice conversation paused'
                          : _sending
                              ? 'Maya is thinking…'
                              : _listening
                                  ? 'Maya is listening…'
                                  : 'Ready to talk',
                      style: titleStyle,
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      offline
                          ? 'Offline guided practice is active while AI reconnects'
                          : _voicePaused
                              ? 'Tap Resume when you are ready'
                              : _listening
                                  ? 'Speak now'
                                  : 'Tap the microphone and speak naturally',
                      textAlign: TextAlign.center,
                      maxLines: 2,
                    ),
                    if (_liveWords.isNotEmpty) ...[
                      const SizedBox(height: 10),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: Theme.of(context).colorScheme.primaryContainer.withValues(alpha: .38),
                          borderRadius: BorderRadius.circular(14),
                        ),
                        child: Text('“$_liveWords”', textAlign: TextAlign.center),
                      ),
                    ],
                    SizedBox(height: compact ? 14 : 20),
                    GestureDetector(
                      onTap: _voicePaused || _sending ? null : _toggleMic,
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 220),
                        width: micSize,
                        height: micSize,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          gradient: LinearGradient(
                            colors: _listening
                                ? [const Color(0xFF9B5CFF), const Color(0xFF5B1DFF)]
                                : [Theme.of(context).colorScheme.primary, const Color(0xFF7B2DFF)],
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: Theme.of(context).colorScheme.primary.withValues(alpha: .28),
                              blurRadius: _listening ? 28 : 16,
                              spreadRadius: _listening ? 5 : 2,
                            ),
                          ],
                        ),
                        child: Icon(
                          _listening ? Icons.stop_rounded : Icons.mic_rounded,
                          color: Colors.white,
                          size: compact ? 40 : 46,
                        ),
                      ),
                    ),
                    const SizedBox(height: 9),
                    Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                      Icon(Icons.circle, size: 8, color: statusColor),
                      const SizedBox(width: 6),
                      Text(_voiceTime(), style: const TextStyle(fontWeight: FontWeight.w800)),
                    ]),
                    SizedBox(height: compact ? 12 : 18),
                    Row(children: [
                      Expanded(
                        child: OutlinedButton(
                          onPressed: _end,
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 11),
                          ),
                          child: const Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                            Icon(Icons.call_end_rounded, color: Colors.red, size: 18),
                            SizedBox(width: 5),
                            Text('End', maxLines: 1, style: TextStyle(fontSize: 12.5)),
                          ]),
                        ),
                      ),
                      const SizedBox(width: 7),
                      Expanded(
                        child: OutlinedButton(
                          onPressed: _togglePause,
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 11),
                          ),
                          child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                            Icon(_voicePaused ? Icons.play_arrow_rounded : Icons.pause_rounded, size: 18),
                            const SizedBox(width: 5),
                            Text(_voicePaused ? 'Resume' : 'Pause', maxLines: 1, style: const TextStyle(fontSize: 12.5)),
                          ]),
                        ),
                      ),
                      const SizedBox(width: 7),
                      Expanded(
                        child: OutlinedButton(
                          onPressed: () async {
                            await _tts.stop();
                            setState(() => _speakerOn = !_speakerOn);
                          },
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 11),
                          ),
                          child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                            Icon(_speakerOn ? Icons.volume_up_rounded : Icons.volume_off_rounded, size: 18),
                            const SizedBox(width: 5),
                            const Text('Audio', maxLines: 1, style: TextStyle(fontSize: 12.5)),
                          ]),
                        ),
                      ),
                    ]),
                    const SizedBox(height: 10),
                    const Row(children: [
                      Expanded(child: _VoiceBenefit(icon: Icons.forum_rounded, title: 'Natural Conversation')),
                      SizedBox(width: 6),
                      Expanded(child: _VoiceBenefit(icon: Icons.verified_rounded, title: 'Real-time Correction')),
                      SizedBox(width: 6),
                      Expanded(child: _VoiceBenefit(icon: Icons.favorite_rounded, title: 'Encouraging')),
                    ]),
                    const SizedBox(height: 6),
                    TextButton.icon(
                      onPressed: _leaveVoiceMode,
                      icon: const Icon(Icons.chat_bubble_outline_rounded),
                      label: const Text('Switch to Text Conversation'),
                    ),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }

'''
    text = replace_between(
        text,
        '  Widget _voiceView() {',
        '  Widget _voiceWave() {',
        voice_func,
        'Maya voice view',
    )
    return text


patch('lib/features/ai_practice/presentation/screens/ai_practice_hub_screen.dart', fix_maya)


# ---------------------------------------------------------------------------
# Learn: keep the 60-week roadmap usable when one or more live RPCs are down.
# Do not fake progress; explicitly show reconnecting state plus the roadmap.
# ---------------------------------------------------------------------------
def fix_learn_hub(text: str) -> str:
    old = r'''                if (snapshot.hasError) {
                  return const AppCard(
                    child: Padding(
                      padding: EdgeInsets.symmetric(vertical: AppSpacing.md),
                      child: Row(
                        children: [
                          Icon(Icons.cloud_off_outlined),
                          SizedBox(width: AppSpacing.md),
                          Expanded(
                            child: Text('Your learning path could not be loaded right now. Pull down or reopen Learn to retry.'),
                          ),
                        ],
                      ),
                    ),
                  );
                }
'''
    new = r'''                if (snapshot.hasError) {
                  return AppCard(
                    onTap: () => context.push(RoutePaths.learningPath),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(children: [
                          Container(
                            width: 48,
                            height: 48,
                            alignment: Alignment.center,
                            decoration: BoxDecoration(
                              color: Theme.of(context).colorScheme.primaryContainer,
                              borderRadius: AppRadius.mdAll,
                            ),
                            child: Text(
                              'A1',
                              style: TextStyle(
                                color: Theme.of(context).colorScheme.primary,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                          ),
                          const SizedBox(width: AppSpacing.md),
                          const Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('Your 60-Week Learning Path', style: TextStyle(fontWeight: FontWeight.w800)),
                                SizedBox(height: 3),
                                Text('Live progress is reconnecting. Your roadmap and practice skills are still available.'),
                              ],
                            ),
                          ),
                          const Icon(Icons.chevron_right_rounded),
                        ]),
                        const SizedBox(height: AppSpacing.md),
                        const LinearProgressIndicator(value: 0, minHeight: 7),
                        const SizedBox(height: AppSpacing.sm),
                        const Text('A1 → A2 → B1 → B2 → C1'),
                      ],
                    ),
                  );
                }
'''
    if old in text:
        text = text.replace(old, new, 1)
    elif 'Live progress is reconnecting. Your roadmap' not in text:
        raise SystemExit('Learn hub error marker not found')

    text = text.replace(
        'padding: const EdgeInsets.all(AppSpacing.base),\n          children: [\n            FutureBuilder<List<dynamic>>(',
        'padding: const EdgeInsets.fromLTRB(AppSpacing.base, AppSpacing.base, AppSpacing.base, 120),\n          children: [\n            FutureBuilder<List<dynamic>>(',
        1,
    )
    return text


patch('lib/features/learn/presentation/screens/learn_hub_screen.dart', fix_learn_hub)


def fix_learning_path(text: str) -> str:
    start = "    if (_error != null) {\n"
    end = "\n    final currentWeek = int.tryParse((_state['current_week'] ?? 1).toString()) ?? 1;"
    replacement = r'''    if (_error != null) {
      const levels = <(String, String)>[
        ('A1', 'Weeks 1–12 · Foundations'),
        ('A2', 'Weeks 13–24 · Everyday communication'),
        ('B1', 'Weeks 25–36 · Independent speaking'),
        ('B2', 'Weeks 37–48 · Confident communication'),
        ('C1', 'Weeks 49–60 · Advanced fluency'),
      ];
      return Scaffold(
        appBar: const _LearningAppBar(),
        body: RefreshIndicator(
          onRefresh: _load,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(AppSpacing.base, AppSpacing.base, AppSpacing.base, 40),
            children: [
              AppCard(
                child: Column(children: [
                  Icon(Icons.cloud_sync_outlined, size: 44, color: Theme.of(context).colorScheme.primary),
                  const SizedBox(height: AppSpacing.sm),
                  Text('Learning path is reconnecting', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
                  const SizedBox(height: AppSpacing.xs),
                  const Text('Your 60-week roadmap is still available below. Live week progress will refresh automatically when the service reconnects.', textAlign: TextAlign.center),
                  const SizedBox(height: AppSpacing.md),
                  FilledButton.icon(onPressed: _load, icon: const Icon(Icons.refresh_rounded), label: const Text('Refresh live progress')),
                ]),
              ),
              const SizedBox(height: AppSpacing.lg),
              Text('60-Week Roadmap', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
              const SizedBox(height: AppSpacing.sm),
              ...levels.map((item) => Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                child: AppCard(
                  child: ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: CircleAvatar(child: Text(item.$1, style: const TextStyle(fontWeight: FontWeight.w800))),
                    title: Text(item.$2, style: const TextStyle(fontWeight: FontWeight.w700)),
                    subtitle: const Text('Progress will sync when the learning service is available.'),
                    trailing: const Icon(Icons.route_outlined),
                  ),
                ),
              )),
            ],
          ),
        ),
      );
    }
'''
    text = replace_between(text, start, end, replacement, 'Learning path error state')
    return text


patch('lib/features/learn/presentation/screens/learning_path_screen.dart', fix_learning_path)


# ---------------------------------------------------------------------------
# Achievements: when the stats RPC is unavailable, keep the achievement catalog
# visible and mark only locally-known onboarding status. No fake server stats.
# ---------------------------------------------------------------------------
def fix_achievements(text: str) -> str:
    old = r'''          error: (_, __) => ListView(
            padding: const EdgeInsets.all(AppSpacing.xl),
            children: [
              AppCard(
                child: Column(
                  children: [
                    Icon(Icons.emoji_events_outlined, size: 48, color: Theme.of(context).colorScheme.primary),
                    const SizedBox(height: AppSpacing.md),
                    Text('Achievements are syncing', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
                    const SizedBox(height: AppSpacing.sm),
                    const Text('Your completed activities are safe. Refresh to load the latest badges and milestones.', textAlign: TextAlign.center),
                    const SizedBox(height: AppSpacing.md),
                    FilledButton.tonalIcon(
                      onPressed: () => ref.invalidate(achievementStatsProvider),
                      icon: const Icon(Icons.refresh_rounded),
                      label: const Text('Refresh achievements'),
                    ),
                  ],
                ),
              ),
            ],
          ),
'''
    new = r'''          error: (_, __) => _AchievementsFallback(
            firstStepsUnlocked: onboardingComplete,
            onRetry: () => ref.invalidate(achievementStatsProvider),
          ),
'''
    if old in text:
        text = text.replace(old, new, 1)
    elif '_AchievementsFallback(' not in text:
        raise SystemExit('Achievements error state marker not found')

    marker = 'class _AchievementsGrid extends StatelessWidget {'
    fallback_class = r'''class _AchievementsFallback extends StatelessWidget {
  const _AchievementsFallback({required this.firstStepsUnlocked, required this.onRetry});

  final bool firstStepsUnlocked;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final badges = [
      (title: 'First Steps', subtitle: 'Complete onboarding', icon: Icons.directions_walk, gradient: const [Color(0xFF2563EB), Color(0xFF60A5FA)], unlocked: firstStepsUnlocked),
      (title: '7 Day Streak', subtitle: 'Keep it up!', icon: Icons.local_fire_department_outlined, gradient: const [Color(0xFFEA580C), Color(0xFFFB923C)], unlocked: false),
      (title: '30 Day Streak', subtitle: 'Amazing!', icon: Icons.emoji_events_outlined, gradient: const [Color(0xFF16A34A), Color(0xFF4ADE80)], unlocked: false),
      (title: 'AI Conversation', subtitle: 'Complete 10 chats', icon: Icons.chat_bubble_outline, gradient: const [Color(0xFF9333EA), Color(0xFFC084FC)], unlocked: false),
      (title: '1000 Minutes', subtitle: 'Practice time', icon: Icons.schedule, gradient: const [Color(0xFFD97706), Color(0xFFFBBF24)], unlocked: false),
      (title: 'Vocabulary Hero', subtitle: 'Learn 500 words', icon: Icons.star_border, gradient: const [Color(0xFF0891B2), Color(0xFF67E8F9)], unlocked: false),
    ];

    return ListView(
      padding: const EdgeInsets.fromLTRB(AppSpacing.base, AppSpacing.base, AppSpacing.base, 40),
      children: [
        AppCard(
          child: Column(children: [
            Icon(Icons.cloud_sync_outlined, size: 40, color: Theme.of(context).colorScheme.primary),
            const SizedBox(height: AppSpacing.sm),
            Text('Achievement progress is reconnecting', textAlign: TextAlign.center, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
            const SizedBox(height: AppSpacing.xs),
            const Text('Your badge catalog stays available. Live streak, practice and vocabulary totals will appear after sync.', textAlign: TextAlign.center),
            const SizedBox(height: AppSpacing.md),
            FilledButton.tonalIcon(onPressed: onRetry, icon: const Icon(Icons.refresh_rounded), label: const Text('Refresh progress')),
          ]),
        ),
        const SizedBox(height: AppSpacing.lg),
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: badges.length,
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 3,
            mainAxisSpacing: AppSpacing.lg,
            crossAxisSpacing: AppSpacing.sm,
            childAspectRatio: 0.8,
          ),
          itemBuilder: (context, index) {
            final badge = badges[index];
            return AchievementBadge(
              title: badge.title,
              subtitle: badge.subtitle,
              icon: badge.icon,
              gradient: badge.gradient,
              isUnlocked: badge.unlocked,
            );
          },
        ),
      ],
    );
  }
}

'''
    if 'class _AchievementsFallback extends StatelessWidget' not in text:
        if marker not in text:
            raise SystemExit('Achievements class insertion marker not found')
        text = text.replace(marker, fallback_class + marker, 1)
    return text


patch('lib/features/achievements/presentation/screens/achievements_screen.dart', fix_achievements)


# ---------------------------------------------------------------------------
# Home: remove QA-visible ellipsis from streak/XP helper lines on narrow phones.
# ---------------------------------------------------------------------------
def fix_home_stat(text: str) -> str:
    text = text.replace(
        "final helper = label == 'Day Streak' ? 'Keep it going!' : 'Learn. Practice. Grow.';",
        "final helper = label == 'Day Streak' ? 'Keep it going!' : 'Practice & grow';",
        1,
    )
    old = "Text(helper, maxLines: 1, overflow: TextOverflow.ellipsis, style: textTheme.labelSmall?.copyWith(color: colors.onSurfaceVariant)),"
    new = "FittedBox(fit: BoxFit.scaleDown, alignment: Alignment.centerLeft, child: Text(helper, maxLines: 1, style: textTheme.labelSmall?.copyWith(color: colors.onSurfaceVariant))),"
    if old in text:
        text = text.replace(old, new, 1)
    elif 'FittedBox(fit: BoxFit.scaleDown' not in text:
        raise SystemExit('Home stat helper marker not found')
    return text


patch('lib/features/home/presentation/widgets/stat_chip.dart', fix_home_stat)

print('Testing screenshot fixes v2 applied successfully.')
