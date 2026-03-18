import 'package:flutter/material.dart';

enum ComponentStatus { good, warning, critical }

class DiagnosticComponent {
  final String id;
  final String name;
  final String reading;
  final String unit;
  final ComponentStatus status;
  final IconData icon;
  final double healthPct;
  final String prediction;
  final List<double> history30d;
  final String? dtcCode;
  final String recommendation;
  final int? daysToFailure;
  final double costEstimate;

  const DiagnosticComponent({
    required this.id,
    required this.name,
    required this.reading,
    required this.unit,
    required this.status,
    required this.icon,
    required this.healthPct,
    required this.prediction,
    this.history30d = const [],
    this.dtcCode,
    required this.recommendation,
    this.daysToFailure,
    this.costEstimate = 0,
  });

  Color get statusColor => switch (status) {
    ComponentStatus.critical => const Color(0xFFEF4444),
    ComponentStatus.warning  => const Color(0xFFFBBF24),
    ComponentStatus.good     => const Color(0xFF22C55E),
  };

  String get statusLabel => switch (status) {
    ComponentStatus.critical => 'CRITICAL',
    ComponentStatus.warning  => 'WARNING',
    ComponentStatus.good     => 'GOOD',
  };
}
