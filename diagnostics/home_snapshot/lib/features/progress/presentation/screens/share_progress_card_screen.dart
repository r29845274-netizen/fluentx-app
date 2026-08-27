import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class ShareProgressCardScreen extends StatefulWidget {
  const ShareProgressCardScreen({super.key, this.mode = 'progress'});

  final String mode;

  @override
  State<ShareProgressCardScreen> createState() => _ShareProgressCardScreenState();
}

class _ShareProgressCardScreenState extends State<ShareProgressCardScreen> {
  final GlobalKey _cardKey = GlobalKey();
  Map<String, dynamic> _stats = const {};
  bool _loading = true;
  bool _sharing = false;
  String? _error;

  SupabaseClient get _client => Supabase.instance.client;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await _client.rpc('get_my_share_stats');
      if (!mounted) return;
      setState(() {
        _stats = data is Map ? Map<String, dynamic>.from(data) : <String, dynamic>{};
        _loading = false;
      });
      await _track('share_card_viewed');
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = 'Your share card could not load right now.';
      });
    }
  }

  int _int(String key, [int fallback = 0]) => int.tryParse((_stats[key] ?? fallback).toString()) ?? fallback;
  String _str(String key, [String fallback = '']) => (_stats[key] ?? fallback).toString();

  Future<void> _track(String event) async {
    try {
      await _client.rpc('track_growth_event', params: {
        'p_event_name': event,
        'p_source': 'share_card',
        'p_metadata': {'card_type': widget.mode},
      });
    } catch (_) {}
  }

  Future<File?> _renderPng() async {
    final context = _cardKey.currentContext;
    if (context == null) return null;
    final boundary = context.findRenderObject() as RenderRepaintBoundary?;
    if (boundary == null) return null;
    final image = await boundary.toImage(pixelRatio: 2.5);
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    if (bytes == null) return null;
    final dir = await getTemporaryDirectory();
    final file = File('${dir.path}/fluentx_${widget.mode}_card.png');
    await file.writeAsBytes(bytes.buffer.asUint8List(), flush: true);
    return file;
  }

  Future<void> _share() async {
    if (_sharing) return;
    setState(() => _sharing = true);
    try {
      final file = await _renderPng();
      if (file == null) throw StateError('Card image could not be generated.');
      final level = _str('cefr_level', 'A1');
      final week = _int('current_week', 1);
      final streak = _int('streak_days');
      final text = widget.mode == 'achievement'
          ? 'I am building my English speaking habit with Fluent X — $streak day streak!'
          : 'My Fluent X English progress: $level • Week $week • $streak day streak. Practicing with Maya AI.';
      await Share.shareXFiles([XFile(file.path)], text: text, subject: 'My Fluent X English Progress');
      await _track('share_card_shared');
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Could not open the share sheet. Please try again.')));
    } finally {
      if (mounted) setState(() => _sharing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    return Scaffold(
      appBar: AppBar(title: Text(widget.mode == 'achievement' ? 'Share Achievement' : 'Share Progress')),
      body: SafeArea(
        top: false,
        child: ListView(
          padding: const EdgeInsets.all(18),
          children: [
            if (_error != null) ...[
              Text(_error!, textAlign: TextAlign.center),
              const SizedBox(height: 16),
            ],
            Center(
              child: RepaintBoundary(
                key: _cardKey,
                child: _ProgressShareCard(stats: _stats, mode: widget.mode),
              ),
            ),
            const SizedBox(height: 20),
            FilledButton.icon(
              onPressed: _sharing || _error != null ? null : _share,
              icon: const Icon(Icons.ios_share_rounded),
              label: Text(_sharing ? 'Preparing card…' : 'Share This Card'),
            ),
            const SizedBox(height: 8),
            Text(
              'Your card contains learning progress only — no email, phone number or private conversation text.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}

class _ProgressShareCard extends StatelessWidget {
  const _ProgressShareCard({required this.stats, required this.mode});
  final Map<String, dynamic> stats;
  final String mode;

  int _int(String key, [int fallback = 0]) => int.tryParse((stats[key] ?? fallback).toString()) ?? fallback;
  String _str(String key, [String fallback = '']) => (stats[key] ?? fallback).toString();

  @override
  Widget build(BuildContext context) {
    const purple = Color(0xFF7557F6);
    final streak = _int('streak_days');
    final xp = _int('xp_earned');
    final activeDays = _int('total_active_days');
    final week = _int('current_week', 1);
    final level = _str('cefr_level', 'A1');
    final mastery = _int('weekly_mastery_streak');
    final referrals = _int('successful_referrals');

    return Container(
      width: 360,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFF7F4FF), Color(0xFFE9E2FF)],
        ),
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: purple.withValues(alpha: .18)),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Container(
            width: 44,
            height: 44,
            alignment: Alignment.center,
            decoration: const BoxDecoration(color: purple, shape: BoxShape.circle),
            child: const Text('FX', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900)),
          ),
          const SizedBox(width: 12),
          const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Fluent X', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900)),
            Text('AI English Speaking Coach', style: TextStyle(fontSize: 12)),
          ])),
        ]),
        const SizedBox(height: 24),
        Text(
          mode == 'achievement' ? 'My English Learning Achievement' : 'My English Progress',
          style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w900),
        ),
        const SizedBox(height: 7),
        Text(
          mode == 'achievement'
              ? '$streak day learning streak 🔥'
              : '$level level • Week $week of 60',
          style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: purple),
        ),
        const SizedBox(height: 20),
        Row(children: [
          Expanded(child: _CardStat(value: '$streak', label: 'Day Streak', icon: Icons.local_fire_department_rounded)),
          const SizedBox(width: 8),
          Expanded(child: _CardStat(value: '$xp', label: 'XP', icon: Icons.bolt_rounded)),
          const SizedBox(width: 8),
          Expanded(child: _CardStat(value: '$activeDays', label: 'Active Days', icon: Icons.calendar_month_rounded)),
        ]),
        const SizedBox(height: 9),
        Row(children: [
          Expanded(child: _MiniLine(icon: Icons.workspace_premium_rounded, label: '$mastery weekly mastery streak')),
          const SizedBox(width: 8),
          Expanded(child: _MiniLine(icon: Icons.group_add_rounded, label: '$referrals friends joined')),
        ]),
        const SizedBox(height: 22),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(color: Colors.white.withValues(alpha: .72), borderRadius: BorderRadius.circular(16)),
          child: const Text(
            'Practicing spoken English with Maya AI ✨',
            textAlign: TextAlign.center,
            style: TextStyle(fontWeight: FontWeight.w800),
          ),
        ),
      ]),
    );
  }
}

class _CardStat extends StatelessWidget {
  const _CardStat({required this.value, required this.label, required this.icon});
  final String value;
  final String label;
  final IconData icon;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 7),
    decoration: BoxDecoration(color: Colors.white.withValues(alpha: .74), borderRadius: BorderRadius.circular(15)),
    child: Column(children: [
      Icon(icon, size: 20, color: const Color(0xFF7557F6)),
      const SizedBox(height: 5),
      Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
      Text(label, textAlign: TextAlign.center, style: const TextStyle(fontSize: 9.5)),
    ]),
  );
}

class _MiniLine extends StatelessWidget {
  const _MiniLine({required this.icon, required this.label});
  final IconData icon;
  final String label;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(10),
    decoration: BoxDecoration(color: Colors.white.withValues(alpha: .5), borderRadius: BorderRadius.circular(13)),
    child: Row(children: [
      Icon(icon, size: 17, color: const Color(0xFF7557F6)),
      const SizedBox(width: 6),
      Expanded(child: Text(label, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700))),
    ]),
  );
}
