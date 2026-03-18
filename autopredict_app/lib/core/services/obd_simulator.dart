import 'dart:math';

import '../models/vehicle_data.dart';

/// Simulates realistic OBD-II telemetry as a continuous Stream.
/// Mimics real driving patterns: idle → accelerate → cruise → decelerate.
class OBDSimulator {
  static final _rng = Random();

  // Drive state
  double _speed = 0;
  double _rpm = 800;
  double _coolant = 72;
  double _fuel = 74.0;
  double _throttle = 0;
  double _oilTemp = 70;
  double _voltage = 12.6;
  double _speedAccumulator = 0;
  int _tickCount = 0;

  // Drive phase: 0=idle, 1=accel, 2=cruise, 3=decel
  int _phase = 0;
  int _phaseCounter = 0;

  Stream<VehicleData> stream({Duration interval = const Duration(milliseconds: 800)}) async* {
    while (true) {
      await Future.delayed(interval);
      yield _tick();
    }
  }

  VehicleData _tick() {
    _phaseCounter++;

    // Cycle through driving phases randomly
    if (_phaseCounter > _rng.nextInt(20) + 10) {
      _phase = _rng.nextInt(4);
      _phaseCounter = 0;
    }

    switch (_phase) {
      case 0: // idle
        _speed = _lerp(_speed, 0, 0.08);
        _rpm = _lerp(_rpm, 750 + _rng.nextDouble() * 100, 0.1);
        _throttle = _lerp(_throttle, 0, 0.15);
      case 1: // accelerate
        _speed = _lerp(_speed, 60 + _rng.nextDouble() * 40, 0.04);
        _rpm = _lerp(_rpm, 2200 + _rng.nextDouble() * 800, 0.06);
        _throttle = _lerp(_throttle, 55 + _rng.nextDouble() * 20, 0.1);
      case 2: // cruise
        _speed = _lerp(_speed, 45 + _rng.nextDouble() * 20, 0.02);
        _rpm = _lerp(_rpm, 1600 + _rng.nextDouble() * 300, 0.03);
        _throttle = _lerp(_throttle, 25 + _rng.nextDouble() * 10, 0.05);
      case 3: // decelerate
        _speed = _lerp(_speed, 10 + _rng.nextDouble() * 15, 0.06);
        _rpm = _lerp(_rpm, 1000 + _rng.nextDouble() * 200, 0.08);
        _throttle = _lerp(_throttle, 5, 0.12);
    }

    // Gradual warm-up of coolant and oil
    _coolant = _lerp(_coolant, _speed > 5 ? 88 + _rng.nextDouble() * 4 : 72, 0.005);
    _oilTemp = _lerp(_oilTemp, _speed > 5 ? 95 + _rng.nextDouble() * 5 : 70, 0.004);

    // Fuel slowly depletes
    if (_speed > 2) _fuel = (_fuel - 0.0012).clamp(0, 100);

    // Voltage fluctuates slightly
    _voltage = 12.5 + _rng.nextDouble() * 0.4;

    // Rolling avg speed
    _speedAccumulator += _speed;
    _tickCount++;

    return VehicleData(
      speedMph: double.parse(_speed.toStringAsFixed(1)),
      rpm: double.parse(_rpm.toStringAsFixed(0)),
      coolantTempC: double.parse(_coolant.toStringAsFixed(1)),
      fuelLevelPct: double.parse(_fuel.toStringAsFixed(1)),
      batteryVoltage: double.parse(_voltage.toStringAsFixed(2)),
      throttlePct: double.parse(_throttle.toStringAsFixed(1)),
      oilTempC: double.parse(_oilTemp.toStringAsFixed(1)),
      tyrePressureFl: 31.5 + _rng.nextDouble() * 1.5,
      tyrePressureFr: 31.8 + _rng.nextDouble() * 1.2,
      tyrePressureRl: 31.2 + _rng.nextDouble() * 1.8,
      tyrePressureRr: 31.6 + _rng.nextDouble() * 1.4,
      fuelConsumptionL100: _speed > 5
          ? double.parse((6 + (_speed / 30) * 4).toStringAsFixed(1))
          : 0,
      avgSpeedMph: _tickCount > 0
          ? double.parse((_speedAccumulator / _tickCount).toStringAsFixed(1))
          : 0,
      engineStatus: _speed < 1 ? 'idle' : 'running',
      dtcCodes: const [],
    );
  }

  static double _lerp(double current, double target, double t) =>
      current + (target - current) * t;
}
