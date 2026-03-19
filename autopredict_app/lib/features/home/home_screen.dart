import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/colors.dart';
import '../../core/providers/vehicle_provider.dart';
import '../../shared/widgets/stat_card.dart';
import '../../shared/widgets/speedometer_gauge.dart';
import '../../shared/widgets/vehicle_pod.dart';
import '../../shared/widgets/car_top_view.dart';
import '../../shared/widgets/floating_nav_bar.dart';
import '../battery/battery_screen.dart';
import '../parking/parking_screen.dart';
import '../chat/chat_screen.dart';
import 'settings_tab.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});
  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  @override
  Widget build(BuildContext context) {
    final navIndex = ref.watch(homeNavIndexProvider);
    final colors = context.appColors;
    return Scaffold(
      backgroundColor: colors.scaffoldBg,
      body: IndexedStack(
        index: navIndex,
        children: [
          _DashboardTab(),
          BatteryScreen(),
          ParkingScreen(),
          ChatScreen(),
          SettingsTab(),
        ],
      ),
      bottomNavigationBar: FloatingNavBar(
        currentIndex: navIndex,
        onTap: (i) => ref.read(homeNavIndexProvider.notifier).state = i,
      ),
    );
  }
}

class _DashboardTab extends ConsumerWidget {
  const _DashboardTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final vehicleAsync = ref.watch(vehicleStreamProvider);
    final driverScore = ref.watch(driverScoreProvider);

    return vehicleAsync.when(
      loading: () => const _DashboardLayout(
        vehicle: null, driverScore: 100,
      ),
      error: (_, __) => const _DashboardLayout(vehicle: null, driverScore: 100),
      data: (v) => _DashboardLayout(vehicle: v, driverScore: driverScore),
    );
  }
}

class _DashboardLayout extends ConsumerWidget {
  final vehicle;
  final double driverScore;
  const _DashboardLayout({required this.vehicle, required this.driverScore});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.appColors;
    final v = vehicle;
    final speed = v?.speedMph ?? 0.0;
    final fuel = v?.fuelLevelPct ?? 74.0;
    final coolant = v?.coolantTempC ?? 72.0;
    final battery = v?.batteryVoltage ?? 12.6;
    final rpm = v?.rpm ?? 800.0;
    final consumption = v?.fuelConsumptionL100 ?? 8.5;
    final avgSpeed = v?.avgSpeedMph ?? 0.0;

    return LayoutBuilder(
      builder: (context, constraints) {
        final w = constraints.maxWidth;
        final cardW = (w - 32 - 20) / 3;

        return SafeArea(
          child: SingleChildScrollView(
            physics: const BouncingScrollPhysics(),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  const SizedBox(height: 4),

                  // ── Header ──────────────────────────────────────────────
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Dashboard',
                              style: GoogleFonts.inter(
                                  fontSize: 20, fontWeight: FontWeight.w700, color: colors.textPrimary)),
                          Text(v == null ? 'Connecting…' : 'Live · ${v.engineStatus.toUpperCase()}',
                              style: GoogleFonts.inter(
                                  fontSize: 11, fontWeight: FontWeight.w400, color: colors.textSecondary)),
                        ],
                      ),
                      // Driver Score badge
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: _scoreColor(driverScore).withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(rFull),
                          border: Border.all(color: _scoreColor(driverScore).withValues(alpha: 0.4)),
                        ),
                        child: Row(children: [
                          Icon(Icons.shield_outlined, size: 14, color: _scoreColor(driverScore)),
                          const SizedBox(width: 4),
                          Text('${driverScore.toInt()}',
                              style: GoogleFonts.inter(
                                fontSize: 13, fontWeight: FontWeight.w700,
                                color: _scoreColor(driverScore),
                              )),
                        ]),
                      ),
                    ],
                  ),

                  const SizedBox(height: 14),

                  // ── Service Advisor Alert ─────────────────────────────────
                  GestureDetector(
                    onTap: () {
                      // Switch to AI Chat tab (index 3)
                      ref.read(homeNavIndexProvider.notifier).state = 3;
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                      decoration: BoxDecoration(
                        color: kDanger.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(rMD),
                        border: Border.all(color: kDanger.withValues(alpha: 0.35)),
                      ),
                      child: Row(children: [
                        Container(
                          width: 32, height: 32,
                          decoration: const BoxDecoration(color: kDanger, shape: BoxShape.circle),
                          child: const Icon(Icons.support_agent, size: 16, color: Colors.white),
                        ),
                        const SizedBox(width: 10),
                        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text('⚠️ Service Advisor Alert',
                              style: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w700, color: kDanger)),
                          Text('AI detected an issue · Tap to talk to service advisor',
                              style: GoogleFonts.inter(fontSize: 11, color: kDanger.withValues(alpha: 0.75))),
                        ])),
                        Icon(Icons.arrow_forward_ios, size: 13, color: kDanger),
                      ]),
                    ),
                  ),

                  const SizedBox(height: 14),
                  Row(
                    children: [
                      SizedBox(
                        width: cardW,
                        child: StatCard(
                          label: 'Consumption',
                          value: consumption.toStringAsFixed(1),
                          unit: 'L/100',
                          tint: colors.statCardGradient1[0],
                          gradient: colors.statCardGradient1,
                        ),
                      ),
                      const SizedBox(width: 10),
                      SizedBox(
                        width: cardW,
                        child: StatCard(
                          label: 'Avg. speed',
                          value: avgSpeed.toStringAsFixed(1),
                          unit: 'mph',
                          tint: colors.statCardGradient2[0],
                          gradient: colors.statCardGradient2,
                        ),
                      ),
                      const SizedBox(width: 10),
                      SizedBox(
                        width: cardW,
                        child: StatCard(
                          label: 'RPM',
                          value: rpm.toStringAsFixed(0),
                          unit: 'rpm',
                          tint: colors.statCardGradient3[0],
                          gradient: colors.statCardGradient3,
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 16),

                  // ── Speedometer ──────────────────────────────────────────
                  SpeedometerGauge(value: speed, max: 120),

                  const SizedBox(height: 6),

                  // ── Fuel & Battery row ───────────────────────────────────
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.local_gas_station, size: 15, color: kFuelOrange),
                      const SizedBox(width: 4),
                      Text('${fuel.toStringAsFixed(0)}%',
                          style: GoogleFonts.inter(
                              fontSize: 13, fontWeight: FontWeight.w600, color: kFuelOrange)),
                      const SizedBox(width: 20),
                      Icon(Icons.battery_charging_full, size: 15, color: kGood),
                      const SizedBox(width: 4),
                      Text('${battery.toStringAsFixed(1)}V',
                          style: GoogleFonts.inter(
                              fontSize: 13, fontWeight: FontWeight.w600, color: kGood)),
                    ],
                  ),

                  const SizedBox(height: 16),

                  // ── Vehicle row ───────────────────────────────────────────
                  SizedBox(
                    height: 310,
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Flexible(
                          flex: 1,
                          child: SizedBox(
                            height: 270,
                            child: VehiclePod(
                              headerIcon: Icons.light_outlined,
                              topIcon: Icons.light_outlined,
                              topValue: '${coolant.toStringAsFixed(0)}°C',
                              topStatus: 'Normal',
                              middleIcon: Icons.thermostat_outlined,
                              middleValue: '${coolant.toStringAsFixed(0)}°C',
                              middleStatus: _coolantStatus(coolant),
                              bottomIcon: Icons.local_gas_station,
                              bottomValue: '${fuel.toStringAsFixed(0)}%',
                              bottomColor: fuel < 15 ? kDanger : kGood,
                              alignRight: false,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        const SizedBox(
                          width: 200,
                          child: CarTopView(timeMin: 0, distanceMi: 0),
                        ),
                        const SizedBox(width: 8),
                        Flexible(
                          flex: 1,
                          child: SizedBox(
                            height: 270,
                            child: VehiclePod(
                              headerIcon: Icons.directions_car_outlined,
                              topIcon: Icons.directions_car_outlined,
                              topValue: '${speed.toStringAsFixed(0)}',
                              topStatus: 'mph',
                              middleIcon: Icons.thermostat_outlined,
                              middleValue: '${rpm.toStringAsFixed(0)}',
                              middleStatus: 'RPM',
                              bottomIcon: Icons.battery_charging_full_outlined,
                              bottomValue: '${battery.toStringAsFixed(1)}V',
                              bottomColor: battery < 11.8 ? kWarning : kGood,
                              alignRight: true,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 16),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Color _scoreColor(double s) {
    if (s >= 85) return kGood;
    if (s >= 65) return kWarning;
    return kDanger;
  }

  String _coolantStatus(double t) {
    if (t < 60) return 'Warming';
    if (t > 105) return 'HOT!';
    return 'Normal';
  }
}
