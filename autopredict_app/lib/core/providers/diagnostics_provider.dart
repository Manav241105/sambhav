import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/diagnostic_component.dart';
import '../services/api_service.dart';

final _api = ApiService();

const _icons = <String, IconData>{
  'brake_pads': Icons.disc_full,
  'battery': Icons.battery_charging_full,
  'engine_oil': Icons.oil_barrel,
  'coolant_system': Icons.thermostat,
  'tires': Icons.tire_repair,
  'air_filter': Icons.air,
};

/// Per-part health for the owner's car, straight from the API's assessment
/// (`diagnosis.parts`). Nothing here is invented: no readings, costs or trends
/// are shown unless the server provides them.
final diagnosticsProvider = FutureProvider<List<DiagnosticComponent>>((ref) async {
  final vehicle = await _api.getVehicleDetail();
  final diagnosis = Map<String, dynamic>.from(vehicle['diagnosis'] as Map? ?? {});
  final parts = List<Map<String, dynamic>>.from(
    (diagnosis['parts'] as List? ?? []).map((p) => Map<String, dynamic>.from(p as Map)),
  );

  final components = parts.map((p) {
    final wear = (p['wear_ratio'] as num? ?? 0).toDouble();
    final risk = (p['risk'] as num? ?? 0).toDouble();
    final rul = p['rul_days'] as int?;
    final kmLow = p['km_left_low'] as int?;
    final kmHigh = p['km_left_high'] as int?;
    final evidence = List<String>.from(p['evidence'] as List? ?? const []);

    final status = risk >= 0.9
        ? ComponentStatus.critical
        : risk >= 0.75
            ? ComponentStatus.warning
            : ComponentStatus.good;

    final prediction = kmLow != null && kmHigh != null
        ? 'About ${_km(kmLow)}–${_km(kmHigh)} km left${rul != null ? ' (~$rul days at your usage)' : ''}'
        : rul != null
            ? 'About $rul days left'
            : 'No estimate yet';

    final basis = evidence.map((e) => e.replaceAll('_', ' ')).join(', ');
    final recommendation = switch (status) {
      ComponentStatus.critical => 'Book a service now.',
      ComponentStatus.warning => 'Plan a service soon.',
      ComponentStatus.good => 'No action needed.',
    };

    return DiagnosticComponent(
      id: p['part'] as String,
      name: p['name'] as String,
      reading: (wear * 100).toStringAsFixed(0),
      unit: '% of typical life used',
      status: status,
      icon: _icons[p['part']] ?? Icons.build,
      healthPct: ((1 - wear.clamp(0.0, 1.0)) * 100),
      prediction: prediction,
      daysToFailure: rul,
      recommendation: basis.isEmpty ? recommendation : '$recommendation Based on: $basis.',
    );
  }).toList();

  // Most urgent first.
  components.sort((a, b) => a.healthPct.compareTo(b.healthPct));
  return components;
});

String _km(int km) => km >= 1000 ? '${(km / 1000).toStringAsFixed(km >= 10000 ? 0 : 1)}k' : '$km';
