import 'package:flutter/material.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/typography.dart';

/// White arch pod shape (left or right side of vehicle section)
class VehiclePod extends StatelessWidget {
  final IconData topIcon;
  final String topValue;
  final String topStatus;
  final IconData bottomIcon;
  final String bottomValue;
  final Color bottomColor;
  final IconData headerIcon;
  final bool alignRight;

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
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: kPodBg,
        borderRadius: BorderRadius.circular(rLG),
        boxShadow: const [cardShadow],
      ),
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Header icon (small, top of pod)
          Align(
            alignment: alignRight ? Alignment.centerRight : Alignment.centerLeft,
            child: Icon(headerIcon, size: 18, color: kMid),
          ),

          // Top stat button
          _NeuButton(icon: topIcon),
          Text(topValue, style: kCaption()),
          Text(topStatus, style: kCaption().copyWith(fontSize: 10)),

          const SizedBox(height: 4),

          // Bottom stat button
          _NeuButton(icon: bottomIcon),
          Text(
            bottomValue,
            style: kCaption().copyWith(
              color: bottomColor,
              fontWeight: FontWeight.w700,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}

class _NeuButton extends StatelessWidget {
  final IconData icon;
  const _NeuButton({required this.icon});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 48,
      height: 48,
      decoration: BoxDecoration(
        color: kNeuBg,
        shape: BoxShape.circle,
        boxShadow: [neuShadowLight, neuShadowDark],
      ),
      child: Icon(icon, size: 20, color: kMid),
    );
  }
}
