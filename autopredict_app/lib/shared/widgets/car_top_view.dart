import 'package:flutter/material.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/typography.dart';

/// Glowing dark blue car top-view center piece
class CarTopView extends StatelessWidget {
  final int timeMin;
  final int distanceMi;

  const CarTopView({super.key, required this.timeMin, required this.distanceMi});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 120,
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF0D1B4B), Color(0xFF1A3A6B)],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
        borderRadius: BorderRadius.circular(rLG),
        boxShadow: [
          BoxShadow(
            color: kCarGlow.withOpacity(0.4),
            blurRadius: 30,
            spreadRadius: 5,
          ),
        ],
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Car icon (replace with SVG top-view asset)
          Icon(Icons.directions_car, size: 56, color: const Color(0xFF64B5F6)),
          const SizedBox(height: 12),

          // Time chip
          _InfoChip(icon: Icons.timer_outlined, label: '$timeMin min'),
          const SizedBox(height: 6),

          // Distance chip
          _InfoChip(icon: Icons.swap_horiz, label: '$distanceMi mi'),
        ],
      ),
    );
  }
}

class _InfoChip extends StatelessWidget {
  final IconData icon;
  final String label;
  const _InfoChip({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        borderRadius: BorderRadius.circular(rFull),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: Colors.white70),
          const SizedBox(width: 4),
          Text(label, style: kCaption(color: Colors.white70)),
        ],
      ),
    );
  }
}
