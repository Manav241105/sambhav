import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/material.dart';
import '../models/diagnostic_component.dart';
import '../services/api_service.dart';

final _api = ApiService();

final diagnosticsProvider = FutureProvider<List<DiagnosticComponent>>((ref) async {
  // Try to get real data from backend
  Map<String, dynamic> vehicle = {};
  try {
    vehicle = await _api.getVehicle();
  } catch (_) {}

  final diagnosis = vehicle['diagnosis'] as Map? ?? {};
  final component = diagnosis['predicted_component'] as String? ?? 'brake_pads';
  final rulDays = diagnosis['rul_days'] as int? ?? 12;

  // Build components list with real + static data
  return [
    DiagnosticComponent(
      id: 'brake_pads',
      name: 'Brake Pads',
      reading: '2.1',
      unit: 'mm',
      status: ComponentStatus.critical,
      icon: Icons.disc_full,
      healthPct: 15,
      prediction: 'Estimated failure in ~$rulDays days at current wear rate',
      daysToFailure: rulDays,
      costEstimate: 4500,
      dtcCode: 'C0045',
      recommendation: 'Replace immediately. Pads below minimum 3mm safety threshold.',
      history30d: _trend(100, 15, 30),
    ),
    DiagnosticComponent(
      id: 'battery',
      name: 'Battery',
      reading: '11.8',
      unit: 'V',
      status: ComponentStatus.warning,
      icon: Icons.battery_3_bar,
      healthPct: 62,
      prediction: 'Weak charge — may fail to start in cold weather',
      daysToFailure: 45,
      costEstimate: 3200,
      dtcCode: null,
      recommendation: 'Load test battery. Consider replacement before monsoon season.',
      history30d: _trend(90, 62, 30),
    ),
    DiagnosticComponent(
      id: 'coolant',
      name: 'Coolant',
      reading: '88',
      unit: '°C',
      status: ComponentStatus.good,
      icon: Icons.water_drop_outlined,
      healthPct: 85,
      prediction: 'Normal operating range. Next flush in ~6 months.',
      costEstimate: 800,
      recommendation: 'Coolant level and quality are good.',
      history30d: _trend(80, 85, 30),
    ),
    DiagnosticComponent(
      id: 'engine',
      name: 'Engine',
      reading: '94',
      unit: '%',
      status: ComponentStatus.good,
      icon: Icons.settings_input_component_outlined,
      healthPct: 94,
      prediction: 'Engine in excellent condition.',
      costEstimate: 0,
      recommendation: 'No action required. Oil change due in 2,400 km.',
      history30d: _trend(88, 94, 30),
    ),
    DiagnosticComponent(
      id: 'tires',
      name: 'Tires',
      reading: '28',
      unit: 'PSI',
      status: ComponentStatus.warning,
      icon: Icons.tire_repair,
      healthPct: 58,
      prediction: 'Low pressure detected — affects fuel economy & safety',
      daysToFailure: 60,
      costEstimate: 200,
      recommendation: 'Inflate to 32 PSI. Check for slow puncture.',
      history30d: _trend(75, 58, 30),
    ),
    DiagnosticComponent(
      id: 'transmission',
      name: 'Transmission',
      reading: '87',
      unit: '%',
      status: ComponentStatus.good,
      icon: Icons.settings_suggest,
      healthPct: 87,
      prediction: 'Transmission fluid due for change in ~8,000 km.',
      costEstimate: 1200,
      recommendation: 'Schedule fluid change at next service.',
      history30d: _trend(82, 87, 30),
    ),
  ];
});

/// Generate a realistic 30-day health trend from start to end value
List<double> _trend(double start, double end, int days) {
  final list = <double>[];
  for (int i = 0; i < days; i++) {
    final t = i / (days - 1);
    final noise = (i % 3 == 0) ? -1.5 : 1.0;
    list.add((start + (end - start) * t + noise).clamp(0, 100));
  }
  return list;
}
