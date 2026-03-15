import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/theme/colors.dart';

/// Animated floating car GIF with info circle — no background box, no tap overlays
class CarTopView extends StatefulWidget {
  final int timeMin;
  final int distanceMi;

  const CarTopView({super.key, required this.timeMin, required this.distanceMi});

  @override
  State<CarTopView> createState() => _CarTopViewState();
}

class _CarTopViewState extends State<CarTopView>
    with SingleTickerProviderStateMixin {
  late AnimationController _floatCtrl;
  late Animation<double> _floatAnim;

  @override
  void initState() {
    super.initState();
    _floatCtrl = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
    _floatAnim = Tween<double>(begin: -4.0, end: 4.0).animate(
      CurvedAnimation(parent: _floatCtrl, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _floatCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _floatAnim,
      builder: (_, __) {
        return Transform.translate(
          offset: Offset(0, _floatAnim.value),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            mainAxisSize: MainAxisSize.min,
            children: [
              // Car GIF
              Image.asset(
                'assets/images/car_home.gif',
                width: 200,
                height: 200,
                fit: BoxFit.contain,
              ),

              const SizedBox(height: 8),

              // Info overlay circle
              _OverlayCircle(
                timeMin: widget.timeMin,
                distanceMi: widget.distanceMi,
              ),
            ],
          ),
        );
      },
    );
  }
}

class _OverlayCircle extends StatelessWidget {
  final int timeMin;
  final int distanceMi;
  const _OverlayCircle({required this.timeMin, required this.distanceMi});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 70,
      height: 70,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: Colors.white.withValues(alpha: 0.7),
        border: Border.all(color: kCarGlow.withValues(alpha: 0.45), width: 1),
        boxShadow: [
          BoxShadow(
            color: kCarGlow.withValues(alpha: 0.2),
            blurRadius: 14,
            spreadRadius: 2,
          ),
        ],
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            '$timeMin min',
            style: GoogleFonts.inter(
              fontSize: 10,
              fontWeight: FontWeight.w600,
              color: kDark,
            ),
          ),
          Container(
            width: 20,
            height: 20,
            margin: const EdgeInsets.symmetric(vertical: 2),
            decoration: const BoxDecoration(
              color: kAccent,
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.arrow_forward, size: 11, color: Colors.black),
          ),
          Text(
            '$distanceMi mi',
            style: GoogleFonts.inter(
              fontSize: 10,
              fontWeight: FontWeight.w600,
              color: kDark,
            ),
          ),
        ],
      ),
    );
  }
}
