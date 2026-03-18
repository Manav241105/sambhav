import 'package:flutter/material.dart';

/// Floating car GIF — no background, no tap overlays, no info circle
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
    _floatAnim = Tween<double>(begin: -6.0, end: 6.0).animate(
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
      builder: (_, __) => Transform.translate(
        offset: Offset(0, _floatAnim.value),
        child: Image.asset(
          'assets/images/car_home.gif',
          width: 300,
          height: 300,
          fit: BoxFit.contain,
        ),
      ),
    );
  }
}
