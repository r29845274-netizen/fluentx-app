import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../../core/constants/app_durations.dart';

/// The signature Communication DNA visualization — a 5-axis radar
/// chart, custom-painted (not a generic progress bar) per the product
/// spec's explicit call-out that this is the flagship differentiator.
class CommunicationDnaRadarChart extends StatelessWidget {
  const CommunicationDnaRadarChart({required this.values, super.key, this.size = 280});

  /// Ordered map of axis label → score (0-100). Exactly 5 entries
  /// expected (Fluency, Vocabulary, Grammar, Pronunciation, Confidence).
  final Map<String, int> values;
  final double size;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: 1),
      duration: AppDurations.slow,
      curve: AppDurations.standardCurve,
      builder: (context, progress, _) {
        return SizedBox(
          width: size,
          height: size,
          child: CustomPaint(
            painter: _RadarChartPainter(
              values: values,
              progress: progress,
              gridColor: colorScheme.outline,
              fillColor: colorScheme.primary.withValues(alpha: 0.25),
              strokeColor: colorScheme.primary,
              labelStyle: Theme.of(context).textTheme.labelSmall ?? const TextStyle(fontSize: 11),
              labelColor: colorScheme.onSurfaceVariant,
            ),
          ),
        );
      },
    );
  }
}

class _RadarChartPainter extends CustomPainter {
  _RadarChartPainter({
    required this.values,
    required this.progress,
    required this.gridColor,
    required this.fillColor,
    required this.strokeColor,
    required this.labelStyle,
    required this.labelColor,
  });

  final Map<String, int> values;
  final double progress;
  final Color gridColor;
  final Color fillColor;
  final Color strokeColor;
  final TextStyle labelStyle;
  final Color labelColor;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final maxRadius = size.width / 2 - 32; // leave room for labels
    final axisCount = values.length;
    if (axisCount == 0) return;

    final angleStep = (2 * math.pi) / axisCount;
    const startAngle = -math.pi / 2;

    Offset pointFor(int index, double fraction) {
      final angle = startAngle + angleStep * index;
      return Offset(
        center.dx + maxRadius * fraction * math.cos(angle),
        center.dy + maxRadius * fraction * math.sin(angle),
      );
    }

    // Background grid rings (25/50/75/100%)
    final gridPaint = Paint()
      ..color = gridColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    for (final ring in [0.25, 0.5, 0.75, 1.0]) {
      final path = Path();
      for (var i = 0; i < axisCount; i++) {
        final p = pointFor(i, ring);
        if (i == 0) {
          path.moveTo(p.dx, p.dy);
        } else {
          path.lineTo(p.dx, p.dy);
        }
      }
      path.close();
      canvas.drawPath(path, gridPaint);
    }

    // Axis lines
    for (var i = 0; i < axisCount; i++) {
      canvas.drawLine(center, pointFor(i, 1.0), gridPaint);
    }

    // Data polygon
    final dataPath = Path();
    final entries = values.entries.toList();
    for (var i = 0; i < axisCount; i++) {
      final fraction = (entries[i].value.clamp(0, 100) / 100) * progress;
      final p = pointFor(i, fraction);
      if (i == 0) {
        dataPath.moveTo(p.dx, p.dy);
      } else {
        dataPath.lineTo(p.dx, p.dy);
      }
    }
    dataPath.close();

    canvas.drawPath(dataPath, Paint()..color = fillColor);
    canvas.drawPath(
      dataPath,
      Paint()
        ..color = strokeColor
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2,
    );

    // Data point dots
    for (var i = 0; i < axisCount; i++) {
      final fraction = (entries[i].value.clamp(0, 100) / 100) * progress;
      final p = pointFor(i, fraction);
      canvas.drawCircle(p, 3, Paint()..color = strokeColor);
    }

    // Axis labels
    for (var i = 0; i < axisCount; i++) {
      final labelPoint = pointFor(i, 1.18);
      final textPainter = TextPainter(
        text: TextSpan(text: entries[i].key, style: labelStyle.copyWith(color: labelColor)),
        textDirection: TextDirection.ltr,
        textAlign: TextAlign.center,
      )..layout();
      textPainter.paint(
        canvas,
        Offset(labelPoint.dx - textPainter.width / 2, labelPoint.dy - textPainter.height / 2),
      );
    }
  }

  @override
  bool shouldRepaint(covariant _RadarChartPainter oldDelegate) {
    return oldDelegate.values != values || oldDelegate.progress != progress;
  }
}
