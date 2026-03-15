import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/theme/colors.dart';

/// Pastel gradient stat card — top 3 cards
class StatCard extends StatelessWidget {
  final String label;
  final String value;
  final String unit;
  /// Deprecated flat tint — kept for compat, gradient takes precedence
  final Color tint;
  final List<Color>? gradient;

  const StatCard({
    super.key,
    required this.label,
    required this.value,
    required this.unit,
    required this.tint,
    this.gradient,
  });

  @override
  Widget build(BuildContext context) {
    final grad = gradient ?? [tint, tint];
    return Container(
      height: 80,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: grad,
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(rMD),
        boxShadow: [neuShadowDark, neuShadowLight],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Title
          Text(
            label,
            style: GoogleFonts.inter(
              fontSize: 11,
              fontWeight: FontWeight.w500,
              color: const Color(0xFF8C8C8C),
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          // Value + unit row
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                value,
                style: GoogleFonts.inter(
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                  color: kDark,
                  height: 1.0,
                ),
              ),
              const SizedBox(width: 3),
              Padding(
                padding: const EdgeInsets.only(bottom: 2),
                child: Text(
                  unit,
                  style: GoogleFonts.inter(
                    fontSize: 11,
                    fontWeight: FontWeight.w400,
                    color: const Color(0xFF8C8C8C),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
