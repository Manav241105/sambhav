import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/vehicle_data.dart';
import '../services/obd_simulator.dart';

final _simulator = OBDSimulator();

/// Streams live vehicle telemetry every 800ms
final vehicleStreamProvider = StreamProvider<VehicleData>((ref) {
  return _simulator.stream();
});

/// The latest vehicle data snapshot (convenience)
final vehicleProvider = Provider<VehicleData>((ref) {
  return ref.watch(vehicleStreamProvider).maybeWhen(
    data: (d) => d,
    orElse: () => const VehicleData(),
  );
});

/// Driver score computed from live telemetry (0–100)
final driverScoreProvider = Provider<double>((ref) {
  final v = ref.watch(vehicleProvider);
  double score = 100;

  // Penalise harsh driving signals
  if (v.speedMph > 90) score -= 20;
  else if (v.speedMph > 75) score -= 10;

  if (v.throttlePct > 80) score -= 15;
  else if (v.throttlePct > 60) score -= 8;

  if (v.rpm > 4000) score -= 10;
  else if (v.rpm > 3000) score -= 5;

  if (v.coolantTempC > 105) score -= 15;
  if (v.fuelLevelPct < 10) score -= 5;

  return score.clamp(0, 100);
});

/// Controls which tab the home screen bottom nav shows.
/// Any widget can read/write this to switch tabs programmatically.
final homeNavIndexProvider = StateProvider<int>((ref) => 0);
