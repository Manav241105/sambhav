import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/theme/app_theme.dart';
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
    final colors = context.appColors;

    return Container(
      decoration: BoxDecoration(
        color: colors.neuBg,
        borderRadius: BorderRadius.circular(rLG),
        boxShadow: [colors.neuShadow1, colors.neuShadow2],
      ),
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 8),
      child: FittedBox(
        fit: BoxFit.scaleDown,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            // Header icon
            Align(
              alignment:
                  alignRight ? Alignment.centerRight : Alignment.centerLeft,
              child: _NeuCircle(
                icon: headerIcon,
                iconSize: 12,
                size: 24,
                iconColor: colors.textSecondary,
                glowColor: null,
              ),
            ),

            const SizedBox(height: 4),

            // ── Row 1: Light / Car ────────────────────────────
            _MetricRow(
              icon: topIcon,
              iconColor: const Color(0xFF38BDF8),
              glowColor: const Color(0xFF38BDF8),
              label: alignRight ? 'Status' : 'Light',
              value: topValue,
              valueColor: colors.textPrimary,
              subtext: topStatus,
            ),

            const SizedBox(height: 4),

            // ── Row 2: Temperature ────────────────────────────
            _MetricRow(
              icon: middleIcon ?? Icons.thermostat_outlined,
              iconColor: const Color(0xFFF97316),
              glowColor: const Color(0xFFF97316),
              label: 'Temp',
              value: middleValue ?? '0°F',
              valueColor: const Color(0xFFF97316),
              subtext: middleStatus ?? '100%',
            ),

            const SizedBox(height: 4),

            // ── Row 3: Fuel/Battery ───────────────────────────
            _MetricRow(
              icon: bottomIcon,
              iconColor: kGood,
              glowColor: kGood,
              label: alignRight ? 'Battery' : 'Fuel',
              value: bottomValue,
              valueColor: kGood,
              subtext: '',
            ),
          ],
        ),
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
    final colors = context.appColors;

    return Column(
      children: [
        _NeuCircle(
          icon: icon,
          size: 38,
          iconSize: 17,
          iconColor: iconColor,
          glowColor: glowColor,
        ),
        const SizedBox(height: 2),
        Text(
          label,
          style: GoogleFonts.inter(
            fontSize: 9,
            fontWeight: FontWeight.w500,
            color: colors.textSecondary,
            letterSpacing: 0.3,
          ),
        ),
        Text(
          value,
          style: GoogleFonts.inter(
            fontSize: 11,
            fontWeight: FontWeight.w700,
            color: valueColor,
          ),
        ),
        if (subtext.isNotEmpty)
          Text(
            subtext,
            style: GoogleFonts.inter(
              fontSize: 8,
              fontWeight: FontWeight.w400,
              color: colors.textSecondary,
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
    final colors = context.appColors;

    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: colors.neuBg,
        shape: BoxShape.circle,
        boxShadow: [
          colors.neuShadow1,
          colors.neuShadow2,
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
