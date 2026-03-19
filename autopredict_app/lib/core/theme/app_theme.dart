import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'colors.dart';

// ── Custom ThemeExtension for app-specific semantic colours ──────────────────
class AppColors extends ThemeExtension<AppColors> {
  final Color scaffoldBg;
  final Color surface;
  final Color neuBg;
  final Color navBg;
  final Color navBorder;
  final Color textPrimary;
  final Color textSecondary;
  final Color textHint;
  final BoxShadow neuShadow1;
  final BoxShadow neuShadow2;
  final BoxShadow cardShadowStyle;
  final Color overlayCircleBg;
  final Color overlayCircleBorder;
  final Color gaugeTrackColor;
  final Color inputFill;
  final List<Color> statCardGradient1;
  final List<Color> statCardGradient2;
  final List<Color> statCardGradient3;

  const AppColors({
    required this.scaffoldBg,
    required this.surface,
    required this.neuBg,
    required this.navBg,
    required this.navBorder,
    required this.textPrimary,
    required this.textSecondary,
    required this.textHint,
    required this.neuShadow1,
    required this.neuShadow2,
    required this.cardShadowStyle,
    required this.overlayCircleBg,
    required this.overlayCircleBorder,
    required this.gaugeTrackColor,
    required this.inputFill,
    required this.statCardGradient1,
    required this.statCardGradient2,
    required this.statCardGradient3,
  });

  // ── Light Palette ───────────────────────────────────────────────────────
  static const light = AppColors(
    scaffoldBg: kBg,
    surface: kSurface,
    neuBg: kNeuBg,
    navBg: kNavBg,
    navBorder: Color(0xFFEEEEEE),
    textPrimary: kDark,
    textSecondary: kMid,
    textHint: Color(0xFF6B7280),
    neuShadow1: neuShadowDark,
    neuShadow2: neuShadowLight,
    cardShadowStyle: cardShadow,
    overlayCircleBg: Color(0xB3FFFFFF), // white 70%
    overlayCircleBorder: Color(0x7338BDF8), // kCarGlow 45%
    gaugeTrackColor: Color(0xFFE0E0E0),
    inputFill: kBg,
    statCardGradient1: kCard1Gradient,
    statCardGradient2: kCard2Gradient,
    statCardGradient3: kCard3Gradient,
  );

  // ── Dark Palette ────────────────────────────────────────────────────────
  static const dark = AppColors(
    scaffoldBg: Color(0xFF121218),
    surface: Color(0xFF1E1E2C),
    neuBg: Color(0xFF1A1A26),
    navBg: Color(0xFF1A1A26),
    navBorder: Color(0xFF2A2A3A),
    textPrimary: Color(0xFFE8E8EC),
    textSecondary: Color(0xFF9090A0),
    textHint: Color(0xFF7A7A8C),
    neuShadow1: BoxShadow(
      color: Color(0xFF0A0A10),
      offset: Offset(4, 4),
      blurRadius: 10,
    ),
    neuShadow2: BoxShadow(
      color: Color(0xFF2A2A38),
      offset: Offset(-4, -4),
      blurRadius: 10,
    ),
    cardShadowStyle: BoxShadow(
      color: Color(0x30000000),
      blurRadius: 20,
      offset: Offset(0, 4),
    ),
    overlayCircleBg: Color(0xB31E1E2C), // dark surface 70%
    overlayCircleBorder: Color(0x7338BDF8),
    gaugeTrackColor: Color(0xFF2A2A3A),
    inputFill: Color(0xFF1A1A26),
    statCardGradient1: [Color(0xFF1A3A4A), Color(0xFF163848)],
    statCardGradient2: [Color(0xFF3A3820), Color(0xFF2A3820)],
    statCardGradient3: [Color(0xFF1A3A28), Color(0xFF183830)],
  );

  @override
  AppColors copyWith({
    Color? scaffoldBg,
    Color? surface,
    Color? neuBg,
    Color? navBg,
    Color? navBorder,
    Color? textPrimary,
    Color? textSecondary,
    Color? textHint,
    BoxShadow? neuShadow1,
    BoxShadow? neuShadow2,
    BoxShadow? cardShadowStyle,
    Color? overlayCircleBg,
    Color? overlayCircleBorder,
    Color? gaugeTrackColor,
    Color? inputFill,
    List<Color>? statCardGradient1,
    List<Color>? statCardGradient2,
    List<Color>? statCardGradient3,
  }) {
    return AppColors(
      scaffoldBg: scaffoldBg ?? this.scaffoldBg,
      surface: surface ?? this.surface,
      neuBg: neuBg ?? this.neuBg,
      navBg: navBg ?? this.navBg,
      navBorder: navBorder ?? this.navBorder,
      textPrimary: textPrimary ?? this.textPrimary,
      textSecondary: textSecondary ?? this.textSecondary,
      textHint: textHint ?? this.textHint,
      neuShadow1: neuShadow1 ?? this.neuShadow1,
      neuShadow2: neuShadow2 ?? this.neuShadow2,
      cardShadowStyle: cardShadowStyle ?? this.cardShadowStyle,
      overlayCircleBg: overlayCircleBg ?? this.overlayCircleBg,
      overlayCircleBorder: overlayCircleBorder ?? this.overlayCircleBorder,
      gaugeTrackColor: gaugeTrackColor ?? this.gaugeTrackColor,
      inputFill: inputFill ?? this.inputFill,
      statCardGradient1: statCardGradient1 ?? this.statCardGradient1,
      statCardGradient2: statCardGradient2 ?? this.statCardGradient2,
      statCardGradient3: statCardGradient3 ?? this.statCardGradient3,
    );
  }

  @override
  AppColors lerp(covariant ThemeExtension<AppColors>? other, double t) {
    if (other is! AppColors) return this;
    return AppColors(
      scaffoldBg: Color.lerp(scaffoldBg, other.scaffoldBg, t)!,
      surface: Color.lerp(surface, other.surface, t)!,
      neuBg: Color.lerp(neuBg, other.neuBg, t)!,
      navBg: Color.lerp(navBg, other.navBg, t)!,
      navBorder: Color.lerp(navBorder, other.navBorder, t)!,
      textPrimary: Color.lerp(textPrimary, other.textPrimary, t)!,
      textSecondary: Color.lerp(textSecondary, other.textSecondary, t)!,
      textHint: Color.lerp(textHint, other.textHint, t)!,
      neuShadow1: BoxShadow.lerp(neuShadow1, other.neuShadow1, t)!,
      neuShadow2: BoxShadow.lerp(neuShadow2, other.neuShadow2, t)!,
      cardShadowStyle:
          BoxShadow.lerp(cardShadowStyle, other.cardShadowStyle, t)!,
      overlayCircleBg:
          Color.lerp(overlayCircleBg, other.overlayCircleBg, t)!,
      overlayCircleBorder:
          Color.lerp(overlayCircleBorder, other.overlayCircleBorder, t)!,
      gaugeTrackColor:
          Color.lerp(gaugeTrackColor, other.gaugeTrackColor, t)!,
      inputFill: Color.lerp(inputFill, other.inputFill, t)!,
      statCardGradient1: [
        Color.lerp(statCardGradient1[0], other.statCardGradient1[0], t)!,
        Color.lerp(statCardGradient1[1], other.statCardGradient1[1], t)!,
      ],
      statCardGradient2: [
        Color.lerp(statCardGradient2[0], other.statCardGradient2[0], t)!,
        Color.lerp(statCardGradient2[1], other.statCardGradient2[1], t)!,
      ],
      statCardGradient3: [
        Color.lerp(statCardGradient3[0], other.statCardGradient3[0], t)!,
        Color.lerp(statCardGradient3[1], other.statCardGradient3[1], t)!,
      ],
    );
  }
}

// ── Helper to quickly grab AppColors from context ───────────────────────────
extension AppColorsExtension on BuildContext {
  AppColors get appColors =>
      Theme.of(this).extension<AppColors>() ?? AppColors.light;
}

// ── Full ThemeData builders ─────────────────────────────────────────────────
ThemeData buildLightTheme() {
  return ThemeData(
    brightness: Brightness.light,
    scaffoldBackgroundColor: AppColors.light.scaffoldBg,
    colorScheme: const ColorScheme.light(
      primary: kAccent,
      onPrimary: kDark,
      primaryContainer: Color(0xFFE8FFB0),
      onPrimaryContainer: kDark,
      secondary: kAccentDark,
      onSecondary: kDark,
      surface: kSurface,
      onSurface: kDark,
      outline: Color(0xFFE0E0E0),
    ),
    useMaterial3: true,
    textTheme: GoogleFonts.interTextTheme(ThemeData.light().textTheme),
    appBarTheme: AppBarTheme(
      backgroundColor: AppColors.light.scaffoldBg,
      elevation: 0,
      iconTheme: const IconThemeData(color: kMid),
      titleTextStyle: GoogleFonts.inter(
        fontSize: 22,
        fontWeight: FontWeight.w700,
        color: AppColors.light.textPrimary,
      ),
    ),
    extensions: const [AppColors.light],
  );
}

ThemeData buildDarkTheme() {
  return ThemeData(
    brightness: Brightness.dark,
    scaffoldBackgroundColor: AppColors.dark.scaffoldBg,
    colorScheme: const ColorScheme.dark(
      primary: kAccent,
      onPrimary: kDark,
      primaryContainer: Color(0xFF3A4A10),
      onPrimaryContainer: kAccent,
      secondary: kAccentDark,
      onSecondary: kDark,
      surface: Color(0xFF1E1E2C),
      onSurface: Color(0xFFE8E8EC),
      outline: Color(0xFF2A2A3A),
    ),
    useMaterial3: true,
    textTheme: GoogleFonts.interTextTheme(ThemeData.dark().textTheme),
    appBarTheme: AppBarTheme(
      backgroundColor: AppColors.dark.scaffoldBg,
      elevation: 0,
      iconTheme: const IconThemeData(color: Color(0xFF9090A0)),
      titleTextStyle: GoogleFonts.inter(
        fontSize: 22,
        fontWeight: FontWeight.w700,
        color: AppColors.dark.textPrimary,
      ),
    ),
    extensions: const [AppColors.dark],
  );
}
