import 'package:flutter/material.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/typography.dart';

/// Pastel stat card — top 3 cards (Consumption, Avg Speed, Range)
class StatCard extends StatelessWidget {
  final String label;
  final String value;
  final String unit;
  final Color tint;

  const StatCard({
    super.key,
    required this.label,
    required this.value,
    required this.unit,
    required this.tint,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: tint,
        borderRadius: BorderRadius.circular(rMD),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(label, style: kCaption()),
          const SizedBox(height: 4),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(value, style: kStatValue()),
              const SizedBox(width: 3),
              Padding(
                padding: const EdgeInsets.only(bottom: 3),
                child: Text(unit, style: kStatUnit()),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
