import 'package:flutter/material.dart';

import '../../../core/constants/app_durations.dart';

/// Animated circular progress ring.
///
/// Used for streak/goal completion on Home, quiz scores, and as the
/// building block referenced by the Communication DNA radar chart's
/// surrounding score dial. Animates smoothly whenever [progress]
/// changes rather than jumping instantly, which reads as far more
/// premium than a static [CircularProgressIndicator].
class ProgressRing extends StatelessWidget {
  const ProgressRing({
    required this.progress,
    super.key,
    this.size = 64,
    this.strokeWidth = 6,
    this.centerLabel,
    this.progressColor,
    this.trackColor,
  });

  /// 0.0–1.0
  final double progress;
  final double size;
  final double strokeWidth;
  final Widget? centerLabel;
  final Color? progressColor;
  final Color? trackColor;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final resolvedProgressColor = progressColor ?? colorScheme.primary;
    final resolvedTrackColor = trackColor ?? colorScheme.outline;
    final clamped = progress.clamp(0.0, 1.0);

    return SizedBox(
      width: size,
      height: size,
      child: TweenAnimationBuilder<double>(
        tween: Tween<double>(begin: 0, end: clamped),
        duration: AppDurations.slow,
        curve: AppDurations.standardCurve,
        builder: (context, animatedValue, _) {
          return CustomPaint(
            painter: _ProgressRingPainter(
              progress: animatedValue,
              strokeWidth: strokeWidth,
              progressColor: resolvedProgressColor,
              trackColor: resolvedTrackColor,
            ),
            child: centerLabel != null
                ? Center(child: centerLabel)
                : null,
          );
        },
      ),
    );
  }
}

class _ProgressRingPainter extends CustomPainter {
  _ProgressRingPainter({
    required this.progress,
    required this.strokeWidth,
    required this.progressColor,
    required this.trackColor,
  });

  final double progress;
  final double strokeWidth;
  final Color progressColor;
  final Color trackColor;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = (size.width - strokeWidth) / 2;

    final trackPaint = Paint()
      ..color = trackColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;

    final progressPaint = Paint()
      ..color = progressColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;

    canvas.drawCircle(center, radius, trackPaint);

    const startAngle = -90 * (3.1415926535 / 180);
    final sweepAngle = progress * 2 * 3.1415926535;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      startAngle,
      sweepAngle,
      false,
      progressPaint,
    );
  }

  @override
  bool shouldRepaint(covariant _ProgressRingPainter oldDelegate) {
    return oldDelegate.progress != progress ||
        oldDelegate.progressColor != progressColor ||
        oldDelegate.trackColor != trackColor ||
        oldDelegate.strokeWidth != strokeWidth;
  }
}
