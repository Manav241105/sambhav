import 'package:flutter/material.dart';

// ── App Background ─────────────────────────────────────
const Color kBg         = Color(0xFFEEEEE8);

// ── Stat Cards (3 pastel) ──────────────────────────────
const Color kCardBlue   = Color(0xFFB8E4F4);
const Color kCardYellow = Color(0xFFF5E4A0);
const Color kCardGreen  = Color(0xFFC5F0A8);

// ── Speedometer ────────────────────────────────────────
const Color kGaugeTrack = Color(0xFFE5E5E5);
const Color kGaugeFill  = Color(0xFFB8F040);

// ── Surfaces ───────────────────────────────────────────
const Color kSurface    = Color(0xFFFFFFFF);
const Color kPodBg      = Color(0xFFFFFFFF);
const Color kNeuBg      = Color(0xFFE8E8E4);

// ── Car glow ───────────────────────────────────────────
const Color kCarBase    = Color(0xFF0D1B4B);
const Color kCarGlow    = Color(0xFF38BDF8);

// ── Status values ──────────────────────────────────────
const Color kFuelOrange = Color(0xFFF97316);
const Color kTempYellow = Color(0xFFEAB308);
const Color kGood       = Color(0xFF22C55E);
const Color kDanger     = Color(0xFFEF4444);
const Color kWarning    = Color(0xFFFBBF24);

// ── Typography ─────────────────────────────────────────
const Color kDark       = Color(0xFF111827);
const Color kMid        = Color(0xFF6B7280);
const Color kSubtle     = Color(0xFFE5E7EB);

// ── Bottom Nav ─────────────────────────────────────────
const Color kNavActive  = Color(0xFFB2F040);
const Color kNavIcon    = Color(0xFFAAAAAA);
const Color kNavBg      = Color(0xFFFFFFFF);

// ── Accent / CTAs ──────────────────────────────────────
const Color kAccent     = Color(0xFFC6F54A);
const Color kAccentDark = Color(0xFF8FB82E);

// ── Gradients ──────────────────────────────────────────
const splashGradient = LinearGradient(
  colors: [Color(0xFFC6F54A), Color(0xFF86EFAC)],
  begin: Alignment.topLeft,
  end: Alignment.bottomRight,
);

// ── Corner Radii ───────────────────────────────────────
const double rXS   =  8.0;
const double rSM   = 12.0;
const double rMD   = 16.0;
const double rLG   = 24.0;
const double rXL   = 32.0;
const double rFull = 999.0;

// ── Shadows ────────────────────────────────────────────
const cardShadow = BoxShadow(
  color: Color(0x0D000000),
  blurRadius: 24,
  offset: Offset(0, 4),
);

const floatShadow = BoxShadow(
  color: Color(0x1A000000),
  blurRadius: 32,
  offset: Offset(0, 8),
);

final neuShadowLight = BoxShadow(
  color: Colors.white.withOpacity(0.8),
  offset: const Offset(-3, -3),
  blurRadius: 6,
);

final neuShadowDark = BoxShadow(
  color: const Color(0x22000000),
  offset: const Offset(3, 3),
  blurRadius: 6,
);
