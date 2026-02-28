import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/typography.dart';

class SpeedometerGauge extends StatefulWidget {
  final double value;
  final double max;

  const SpeedometerGauge({super.key, required this.value, this.max = 120});

  @override
  State<SpeedometerGauge> createState() => _SpeedometerGaugeState();
}

class _SpeedometerGaugeState extends State<SpeedometerGauge>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 1200));
    _anim = Tween<double>(begin: 0, end: widget.value)
        .animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeOutCubic));
    _ctrl.forward();
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _anim,
      builder: (_, __) => SizedBox(
        width: 240,
        height: 240,
        child: CustomPaint(
          painter: _SpeedometerPainter(value: _anim.value, max: widget.max),
          child: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  _anim.value.toStringAsFixed(1),
                  style: kGaugeValue(),
                ),
                Text('mph', style: kGaugeSub()),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _SpeedometerPainter extends CustomPainter {
  final double value;
  final double max;

  _SpeedometerPainter({required this.value, required this.max});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width * 0.42;
    // Arc: 150° start, 240° total sweep, gap at bottom
    const startDeg = 150.0;
    const sweepDeg = 240.0;
    final startRad = startDeg * math.pi / 180;
    final sweepRad = sweepDeg * math.pi / 180;
    final rect = Rect.fromCircle(center: center, radius: radius);

    final trackPaint = Paint()
      ..color = kGaugeTrack
      ..strokeWidth = 14
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    // Background track
    canvas.drawArc(rect, startRad, sweepRad, false, trackPaint);

    // Value arc (lime)
    final fillSweep = (value / max).clamp(0.0, 1.0) * sweepRad;
    if (fillSweep > 0) {
      final fillPaint = Paint()
        ..color = kGaugeFill
        ..strokeWidth = 14
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round;
      canvas.drawArc(rect, startRad, fillSweep, false, fillPaint);
    }

    // Tick marks — 13 ticks across 240°
    final tickPaint = Paint()
      ..color = const Color(0xFFCCCCCC)
      ..strokeWidth = 1.5
      ..style = PaintingStyle.stroke;

    for (int i = 0; i <= 12; i++) {
      final angle = startRad + (i / 12) * sweepRad;
      final isMajor = i % 2 == 0;
      final innerR = radius - (isMajor ? 20 : 12);
      final outerR = radius + 3;

      canvas.drawLine(
        center + Offset(math.cos(angle) * innerR, math.sin(angle) * innerR),
        center + Offset(math.cos(angle) * outerR, math.sin(angle) * outerR),
        tickPaint
          ..strokeWidth = isMajor ? 2 : 1
          ..color = const Color(0xFFCCCCCC),
      );

      // Labels at every other major (0, 40, 80, 120)
      if (isMajor && i % 4 == 0) {
        final labelVal = (i / 12 * max).round();
        final labelR = radius + 18;
        final tp = TextPainter(
          text: TextSpan(
            text: '$labelVal',
            style: TextStyle(fontSize: 10, color: kMid, fontWeight: FontWeight.w400),
          ),
          textDirection: TextDirection.ltr,
        )..layout();
        final lx = center.dx + math.cos(angle) * labelR - tp.width / 2;
        final ly = center.dy + math.sin(angle) * labelR - tp.height / 2;
        tp.paint(canvas, Offset(lx, ly));
      }
    }
  }

  @override
  bool shouldRepaint(_SpeedometerPainter old) => old.value != value;
}
