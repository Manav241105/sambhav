import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/theme/colors.dart';

class FloatingNavBar extends StatefulWidget {
  final int currentIndex;
  final ValueChanged<int> onTap;

  const FloatingNavBar({
    super.key,
    required this.currentIndex,
    required this.onTap,
  });

  @override
  State<FloatingNavBar> createState() => _FloatingNavBarState();
}

class _FloatingNavBarState extends State<FloatingNavBar>
    with SingleTickerProviderStateMixin {
  late AnimationController _glowCtrl;
  late Animation<double> _glowAnim;
  // Track which button is being pressed for scale effect
  int? _pressedIndex;

  @override
  void initState() {
    super.initState();
    _glowCtrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 1000))
      ..repeat(reverse: true);
    _glowAnim = Tween<double>(begin: 0.6, end: 1.0)
        .animate(CurvedAnimation(parent: _glowCtrl, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _glowCtrl.dispose();
    super.dispose();
  }

  static const _icons = [
    Icons.bolt,
    Icons.battery_charging_full_outlined,
    Icons.local_parking_outlined,
    Icons.headphones_outlined,
    Icons.settings_outlined,
  ];

  static const _labels = ['Power', 'Battery', 'Park', 'Audio', 'Settings'];

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 80,
      decoration: const BoxDecoration(
        color: kNavBg,
        border: Border(top: BorderSide(color: Color(0xFFEEEEEE), width: 1)),
        boxShadow: [
          BoxShadow(
            color: Color(0x0A000000),
            blurRadius: 20,
            offset: Offset(0, -4),
          ),
        ],
      ),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: List.generate(_icons.length, (i) {
          final isActive = i == widget.currentIndex;
          final isPressed = _pressedIndex == i;

          return GestureDetector(
            onTapDown: (_) {
              setState(() => _pressedIndex = i);
              HapticFeedback.lightImpact();
            },
            onTapUp: (_) {
              setState(() => _pressedIndex = null);
              widget.onTap(i);
            },
            onTapCancel: () => setState(() => _pressedIndex = null),
            child: AnimatedScale(
              scale: isPressed ? 0.88 : 1.0,
              duration: const Duration(milliseconds: 120),
              curve: Curves.easeOut,
              child: AnimatedBuilder(
                animation: _glowAnim,
                builder: (_, child) => AnimatedContainer(
                  duration: const Duration(milliseconds: 250),
                  width: 52,
                  height: 56,
                  decoration: BoxDecoration(
                    color: isActive ? kNavActive : Colors.transparent,
                    borderRadius: BorderRadius.circular(14),
                    boxShadow: isActive
                        ? [
                            BoxShadow(
                              color: kNavActive.withValues(
                                  alpha: _glowAnim.value * 0.6),
                              blurRadius: 16,
                              spreadRadius: 2,
                            ),
                          ]
                        : null,
                    border: isActive
                        ? null
                        : Border.all(
                            color: const Color(0xFFDDDDDD), width: 1.2),
                  ),
                  child: child,
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      _icons[i],
                      size: 20,
                      color: isActive ? Colors.black87 : kNavIcon,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      _labels[i],
                      style: GoogleFonts.inter(
                        fontSize: 9,
                        fontWeight:
                            isActive ? FontWeight.w600 : FontWeight.w400,
                        color: isActive ? Colors.black87 : kNavIcon,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        }),
      ),
    );
  }
}
