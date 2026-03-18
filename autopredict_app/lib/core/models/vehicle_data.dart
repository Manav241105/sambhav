class VehicleData {
  final double speedMph;
  final double rpm;
  final double coolantTempC;
  final double fuelLevelPct;
  final double batteryVoltage;
  final double throttlePct;
  final double oilTempC;
  final double tyrePressureFl;
  final double tyrePressureFr;
  final double tyrePressureRl;
  final double tyrePressureRr;
  final double fuelConsumptionL100;
  final double avgSpeedMph;
  final String engineStatus;
  final List<String> dtcCodes;

  const VehicleData({
    this.speedMph = 0,
    this.rpm = 800,
    this.coolantTempC = 20,
    this.fuelLevelPct = 75,
    this.batteryVoltage = 12.6,
    this.throttlePct = 0,
    this.oilTempC = 20,
    this.tyrePressureFl = 32,
    this.tyrePressureFr = 32,
    this.tyrePressureRl = 32,
    this.tyrePressureRr = 32,
    this.fuelConsumptionL100 = 8.5,
    this.avgSpeedMph = 0,
    this.engineStatus = 'idle',
    this.dtcCodes = const [],
  });

  VehicleData copyWith({
    double? speedMph, double? rpm, double? coolantTempC,
    double? fuelLevelPct, double? batteryVoltage, double? throttlePct,
    double? oilTempC, double? tyrePressureFl, double? tyrePressureFr,
    double? tyrePressureRl, double? tyrePressureRr,
    double? fuelConsumptionL100, double? avgSpeedMph,
    String? engineStatus, List<String>? dtcCodes,
  }) => VehicleData(
    speedMph: speedMph ?? this.speedMph,
    rpm: rpm ?? this.rpm,
    coolantTempC: coolantTempC ?? this.coolantTempC,
    fuelLevelPct: fuelLevelPct ?? this.fuelLevelPct,
    batteryVoltage: batteryVoltage ?? this.batteryVoltage,
    throttlePct: throttlePct ?? this.throttlePct,
    oilTempC: oilTempC ?? this.oilTempC,
    tyrePressureFl: tyrePressureFl ?? this.tyrePressureFl,
    tyrePressureFr: tyrePressureFr ?? this.tyrePressureFr,
    tyrePressureRl: tyrePressureRl ?? this.tyrePressureRl,
    tyrePressureRr: tyrePressureRr ?? this.tyrePressureRr,
    fuelConsumptionL100: fuelConsumptionL100 ?? this.fuelConsumptionL100,
    avgSpeedMph: avgSpeedMph ?? this.avgSpeedMph,
    engineStatus: engineStatus ?? this.engineStatus,
    dtcCodes: dtcCodes ?? this.dtcCodes,
  );
}
