import 'package:flutter/material.dart';
import '../../core/theme/colors.dart';

class FloatingNavBar extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int> onTap;

  const FloatingNavBar({
    super.key,
    required this.currentIndex,
    required this.onTap,
  });

  static const _icons = [
    Icons.bolt,
    Icons.description_outlined,
    Icons.directions_car_outlined,
    Icons.music_note_outlined,
    Icons.settings_outlined,
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      color: kBg,
      child: Container(
        margin: const EdgeInsets.only(bottom: 0),
        decoration: const BoxDecoration(
          color: kNavBg,
          border: Border(top: BorderSide(color: Color(0xFFF0F0F0), width: 1)),
        ),
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 24),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: List.generate(_icons.length, (i) {
            final isActive = i == currentIndex;
            return GestureDetector(
              onTap: () => onTap(i),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: isActive ? kNavActive : Colors.transparent,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  _icons[i],
                  size: 22,
                  color: isActive ? kDark : kNavIcon,
                ),
              ),
            );
          }),
        ),
      ),
    );
  }
}
