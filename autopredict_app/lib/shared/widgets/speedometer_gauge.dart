import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/theme/colors.dart';

class SpeedometerGauge extends StatefulWidget {
  final double value;
  final double max;
  const SpeedometerGauge({super.key, required this.value, this.max = 120});

  @override
  State<SpeedometerGauge> createState() => _SpeedometerGaugeState();
}

class _SpeedometerGaugeState extends State<SpeedometerGauge>
    with TickerProviderStateMixin {
  late AnimationController _needleCtrl;
  late AnimationController _glowCtrl;
  late Animation<double> _needleAnim;
  late Animation<double> _glowAnim;

  @override
  void initState() {
    super.initState();

    // Needle animation
    _needleCtrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 1400));
    _needleAnim = Tween<double>(begin: 0, end: widget.value)
        .animate(CurvedAnimation(parent: _needleCtrl, curve: Curves.easeOutCubic));
    _needleCtrl.forward();

    // Glow pulse animation
    _glowCtrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 1500))
      ..repeat(reverse: true);
    _glowAnim = Tween<double>(begin: 0.4, end: 1.0)
        .animate(CurvedAnimation(parent: _glowCtrl, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _needleCtrl.dispose();
    _glowCtrl.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(SpeedometerGauge oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.value != widget.value) {
      _needleAnim = Tween<double>(begin: _needleAnim.value, end: widget.value)
          .animate(CurvedAnimation(parent: _needleCtrl, curve: Curves.easeOutCubic));
      _needleCtrl
        ..reset()
        ..forward();
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([_needleAnim, _glowAnim]),
      builder: (_, __) {
        final speed = _needleAnim.value;
        return SizedBox(
          width: 270,
          height: 270,
          child: CustomPaint(
            painter: _SpeedometerPainter(value: speed, max: widget.max),
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Glowing speed value
                  Stack(
                    alignment: Alignment.center,
                    children: [
                      // Outer glow
                      Text(
                        speed.toStringAsFixed(1),
                        style: GoogleFonts.inter(
                          fontSize: 50,
                          fontWeight: FontWeight.w800,
                          color: kAccent.withValues(alpha: _glowAnim.value * 0.35),
                          shadows: [
                            Shadow(
                              color: kAccent.withValues(alpha: _glowAnim.value * 0.6),
                              blurRadius: 24,
                            ),
                          ],
                        ),
                      ),
                      // Main text
                      Text(
                        speed.toStringAsFixed(1),
                        style: GoogleFonts.inter(
                          fontSize: 50,
                          fontWeight: FontWeight.w800,
                          color: kDark,
                          height: 1.0,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'mph',
                    style: GoogleFonts.inter(
                      fontSize: 16,
                      fontWeight: FontWeight.w400,
                      color: kMid,
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class _SpeedometerPainter extends CustomPainter {
  final double value;
  final double max;

  _SpeedometerPainter({required this.value, required this.max});

  // Gradient colours: green → yellow → orange → red
  Color _gaugeColor(double t) {
    if (t < 0.33) {
      return Color.lerp(const Color(0xFF22C55E), const Color(0xFFEAB308), t / 0.33)!;
    } else if (t < 0.66) {
      return Color.lerp(const Color(0xFFEAB308), const Color(0xFFF97316), (t - 0.33) / 0.33)!;
    } else {
      return Color.lerp(const Color(0xFFF97316), const Color(0xFFEF4444), (t - 0.66) / 0.34)!;
    }
  }

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width * 0.43;

    const startDeg = 210.0;
    const sweepDeg = 240.0;
    final startRad = startDeg * math.pi / 180;
    final sweepRad = sweepDeg * math.pi / 180;
    final rect = Rect.fromCircle(center: center, radius: radius);

    // ── 1. Background track ───────────────────────────────
    final trackPaint = Paint()
      ..color = const Color(0xFFE0E0E0)
      ..strokeWidth = 16
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;
    canvas.drawArc(rect, startRad, sweepRad, false, trackPaint);

    // ── 2. Gradient filled arc (green→yellow→orange→red) ──
    final fillFrac = (value / max).clamp(0.0, 1.0);
    final fillSweep = fillFrac * sweepRad;

    if (fillSweep > 0.01) {
      const segments = 120;
      final segSweep = fillSweep / segments;
      for (int i = 0; i < segments; i++) {
        final t = i / (segments - 1);
        final segStart = startRad + i * segSweep;
        final paint = Paint()
          ..color = _gaugeColor(t)
          ..strokeWidth = 16
          ..style = PaintingStyle.stroke
          ..strokeCap = (i == 0 || i == segments - 1)
              ? StrokeCap.round
              : StrokeCap.butt;
        canvas.drawArc(rect, segStart, segSweep + 0.01, false, paint);
      }

      // Glow on leading tip of arc
      final tipAngle = startRad + fillSweep;
      final tipPoint = center +
          Offset(math.cos(tipAngle) * radius, math.sin(tipAngle) * radius);
      final glowPaint = Paint()
        ..color = _gaugeColor(fillFrac).withValues(alpha: 0.5)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 10);
      canvas.drawCircle(tipPoint, 8, glowPaint);
    }

    // ── 3. Tick marks (13 ticks = 0…120, every 10mph) ────
    for (int i = 0; i <= 12; i++) {
      final t = i / 12.0;
      final angle = startRad + t * sweepRad;
      final isMajor = i % 2 == 0;
      final tickLen = isMajor ? 11.0 : 6.0;
      final innerR = radius - 24;
      final outerR = innerR + tickLen;

      final active = t <= fillFrac;
      final tickColor = active
          ? _gaugeColor(t).withValues(alpha: 0.9)
          : const Color(0xFFCCCCCC);

      canvas.drawLine(
        center + Offset(math.cos(angle) * innerR, math.sin(angle) * innerR),
        center + Offset(math.cos(angle) * outerR, math.sin(angle) * outerR),
        Paint()
          ..color = tickColor
          ..strokeWidth = isMajor ? 2.2 : 1.2
          ..strokeCap = StrokeCap.round,
      );

      // Speed labels every 30
      if (i % 3 == 0) {
        final labelVal = (t * max).round();
        final labelR = radius + 16;
        final tp = TextPainter(
          text: TextSpan(
            text: '$labelVal',
            style: TextStyle(
              fontSize: 10,
              color: active ? _gaugeColor(t) : kMid,
              fontWeight: active ? FontWeight.w600 : FontWeight.w400,
            ),
          ),
          textDirection: TextDirection.ltr,
        )..layout();
        final lx = center.dx + math.cos(angle) * labelR - tp.width / 2;
        final ly = center.dy + math.sin(angle) * labelR - tp.height / 2;
        tp.paint(canvas, Offset(lx, ly));
      }
    }

    // ── 4. Needle ─────────────────────────────────────────
    final needleAngle = startRad + fillFrac * sweepRad;
    final needleLen = radius - 32;
    final needleEnd = center +
        Offset(math.cos(needleAngle) * needleLen,
            math.sin(needleAngle) * needleLen);

    // Needle shadow glow
    canvas.drawLine(
      center,
      needleEnd,
      Paint()
        ..color = _gaugeColor(fillFrac).withValues(alpha: 0.4)
        ..strokeWidth = 6
        ..strokeCap = StrokeCap.round
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 6),
    );
    // Needle body
    canvas.drawLine(
      center,
      needleEnd,
      Paint()
        ..color = _gaugeColor(fillFrac)
        ..strokeWidth = 2.5
        ..strokeCap = StrokeCap.round,
    );

    // Center pivot ring
    canvas.drawCircle(
        center, 8,
        Paint()..color = _gaugeColor(fillFrac)..style = PaintingStyle.fill);
    canvas.drawCircle(
        center, 8,
        Paint()
          ..color = Colors.white.withValues(alpha: 0.7)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2);
  }

  @override
  bool shouldRepaint(_SpeedometerPainter old) => old.value != value;
}
