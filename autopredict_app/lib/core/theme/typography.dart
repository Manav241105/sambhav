import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

TextStyle kDisplay({Color? color}) => GoogleFonts.inter(
  fontSize: 36, fontWeight: FontWeight.w800, color: color ?? const Color(0xFF111827),
);

TextStyle kTitle({Color? color}) => GoogleFonts.inter(
  fontSize: 22, fontWeight: FontWeight.w700, color: color ?? const Color(0xFF111827),
);

TextStyle kSubtitle({Color? color}) => GoogleFonts.inter(
  fontSize: 17, fontWeight: FontWeight.w600, color: color ?? const Color(0xFF111827),
);

TextStyle kBody({Color? color}) => GoogleFonts.inter(
  fontSize: 15, fontWeight: FontWeight.w400, color: color ?? const Color(0xFF6B7280),
);

TextStyle kCaption({Color? color}) => GoogleFonts.inter(
  fontSize: 11, fontWeight: FontWeight.w500, color: color ?? const Color(0xFF6B7280),
);

TextStyle kLabel({Color? color}) => GoogleFonts.inter(
  fontSize: 12, fontWeight: FontWeight.w600,
  letterSpacing: 0.4, color: color ?? const Color(0xFF6B7280),
);

// Gauge center number
TextStyle kGaugeValue({Color? color}) => GoogleFonts.inter(
  fontSize: 40, fontWeight: FontWeight.w800,
  color: color ?? const Color(0xFF111827), height: 1.0,
);

TextStyle kGaugeSub({Color? color}) => GoogleFonts.inter(
  fontSize: 14, fontWeight: FontWeight.w500, color: color ?? const Color(0xFF6B7280),
);

// Stat card value
TextStyle kStatValue({Color? color}) => GoogleFonts.inter(
  fontSize: 26, fontWeight: FontWeight.w800, color: color ?? const Color(0xFF111827),
);

TextStyle kStatUnit({Color? color}) => GoogleFonts.inter(
  fontSize: 11, fontWeight: FontWeight.w400, color: color ?? const Color(0xFF6B7280),
);
