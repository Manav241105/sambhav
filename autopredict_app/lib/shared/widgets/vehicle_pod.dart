import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/theme/colors.dart';

/// Color-coded neumorphic side panel — 3 metrics with labels
class VehiclePod extends StatelessWidget {
  final IconData topIcon;
  final String topValue;
  final String topStatus;
  final IconData bottomIcon;
  final String bottomValue;
  final Color bottomColor;
  final IconData headerIcon;
  final bool alignRight;
  final IconData? middleIcon;
  final String? middleValue;
  final String? middleStatus;

  const VehiclePod({
    super.key,
    required this.topIcon,
    required this.topValue,
    required this.topStatus,
    required this.bottomIcon,
    required this.bottomValue,
    required this.bottomColor,
    required this.headerIcon,
    this.alignRight = false,
    this.middleIcon,
    this.middleValue,
    this.middleStatus,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: kNeuBg,
        borderRadius: BorderRadius.circular(rLG),
        boxShadow: const [neuShadowDark, neuShadowLight],
      ),
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          // Header icon (small, directional)
          Align(
            alignment:
                alignRight ? Alignment.centerRight : Alignment.centerLeft,
            child: _NeuCircle(
              icon: headerIcon,
              iconSize: 14,
              size: 28,
              iconColor: kMid,
              glowColor: null,
            ),
          ),

          // ── Row 1: Light / Car (blue tint) ───────────────
          _MetricRow(
            icon: topIcon,
            iconColor: const Color(0xFF38BDF8),   // sky blue
            glowColor: const Color(0xFF38BDF8),
            label: alignRight ? 'Status' : 'Light',
            value: topValue,
            valueColor: kDark,
            subtext: topStatus,
          ),

          // ── Row 2: Temperature (orange tint) ─────────────
          _MetricRow(
            icon: middleIcon ?? Icons.thermostat_outlined,
            iconColor: const Color(0xFFF97316),   // orange
            glowColor: const Color(0xFFF97316),
            label: 'Temp',
            value: middleValue ?? '0°F',
            valueColor: const Color(0xFFF97316),
            subtext: middleStatus ?? '100%',
          ),

          // ── Row 3: Fuel/Battery (green tint) ─────────────
          _MetricRow(
            icon: bottomIcon,
            iconColor: kGood,                     // green
            glowColor: kGood,
            label: alignRight ? 'Battery' : 'Fuel',
            value: bottomValue,
            valueColor: kGood,
            subtext: '',
          ),
        ],
      ),
    );
  }
}

class _MetricRow extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final Color glowColor;
  final String label;
  final String value;
  final Color valueColor;
  final String subtext;

  const _MetricRow({
    required this.icon,
    required this.iconColor,
    required this.glowColor,
    required this.label,
    required this.value,
    required this.valueColor,
    required this.subtext,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _NeuCircle(
          icon: icon,
          size: 42,
          iconSize: 19,
          iconColor: iconColor,
          glowColor: glowColor,
        ),
        const SizedBox(height: 3),
        Text(
          label,
          style: GoogleFonts.inter(
            fontSize: 9,
            fontWeight: FontWeight.w500,
            color: kMid,
            letterSpacing: 0.3,
          ),
        ),
        Text(
          value,
          style: GoogleFonts.inter(
            fontSize: 12,
            fontWeight: FontWeight.w700,
            color: valueColor,
          ),
        ),
        if (subtext.isNotEmpty)
          Text(
            subtext,
            style: GoogleFonts.inter(
              fontSize: 9,
              fontWeight: FontWeight.w400,
              color: kMid,
            ),
          ),
      ],
    );
  }
}

class _NeuCircle extends StatelessWidget {
  final IconData icon;
  final double size;
  final double iconSize;
  final Color iconColor;
  final Color? glowColor;

  const _NeuCircle({
    required this.icon,
    required this.size,
    required this.iconSize,
    required this.iconColor,
    required this.glowColor,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: kNeuBg,
        shape: BoxShape.circle,
        boxShadow: [
          neuShadowDark,
          neuShadowLight,
          if (glowColor != null)
            BoxShadow(
              color: glowColor!.withValues(alpha: 0.18),
              blurRadius: 10,
              spreadRadius: 1,
            ),
        ],
      ),
      child: Icon(icon, size: iconSize, color: iconColor),
    );
  }
}
