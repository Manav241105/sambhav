import 'package:flutter/material.dart';

// ── App Background ─────────────────────────────────────
const Color kBg         = Color(0xFFF2F3F5);

// ── Stat Cards (3 pastel gradient tints) ──────────────
const Color kCardBlue   = Color(0xFFB8E4F4);
const Color kCardYellow = Color(0xFFF5E4A0);
const Color kCardGreen  = Color(0xFFC5F0A8);

// Card gradient pairs
const List<Color> kCard1Gradient = [Color(0xFFB8E4F4), Color(0xFF76D7F0)]; // blue→cyan
const List<Color> kCard2Gradient = [Color(0xFFF5E4A0), Color(0xFFD4F0A0)]; // yellow→pale green
const List<Color> kCard3Gradient = [Color(0xFFC5F0A8), Color(0xFF96E8C0)]; // green→mint

// ── Speedometer ────────────────────────────────────────
const Color kGaugeTrack = Color(0xFFE0E0E0);
const Color kGaugeFill  = Color(0xFFC8FF5F);   // spec: #C8FF5F

// ── Surfaces ───────────────────────────────────────────
const Color kSurface    = Color(0xFFFFFFFF);
const Color kPodBg      = Color(0xFFFFFFFF);
const Color kNeuBg      = Color(0xFFF2F3F5);   // same as bg for neumorphism base

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
const Color kDark       = Color(0xFF2C2C2C);   // spec: #2C2C2C
const Color kMid        = Color(0xFF8C8C8C);   // spec: #8C8C8C
const Color kSubtle     = Color(0xFFE5E7EB);

// ── Bottom Nav ─────────────────────────────────────────
const Color kNavActive  = Color(0xFFC7FF5E);   // spec: #C7FF5E
const Color kNavIcon    = Color(0xFFAAAAAA);
const Color kNavBg      = Color(0xFFFFFFFF);

// ── Accent / CTAs ──────────────────────────────────────
const Color kAccent     = Color(0xFFC7FF5E);   // spec: #C7FF5E
const Color kAccentDark = Color(0xFF8FB82E);

// ── Gradients ──────────────────────────────────────────
const splashGradient = LinearGradient(
  colors: [Color(0xFFC7FF5E), Color(0xFF86EFAC)],
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

// ── Neumorphic Shadows ─────────────────────────────────
// Per spec: offset(4,4) blur(10) #d1d1d1 + offset(-4,-4) blur(10) #ffffff
const neuShadowDark = BoxShadow(
  color: Color(0xFFD1D1D1),
  offset: Offset(4, 4),
  blurRadius: 10,
);

const neuShadowLight = BoxShadow(
  color: Color(0xFFFFFFFF),
  offset: Offset(-4, -4),
  blurRadius: 10,
);

// ── Card Shadow ────────────────────────────────────────
const cardShadow = BoxShadow(
  color: Color(0x14000000),
  blurRadius: 20,
  offset: Offset(0, 4),
);

const floatShadow = BoxShadow(
  color: Color(0x1A000000),
  blurRadius: 32,
  offset: Offset(0, 8),
);
