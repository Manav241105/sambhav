import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/colors.dart';
import '../../shared/widgets/stat_card.dart';
import '../../shared/widgets/speedometer_gauge.dart';
import '../../shared/widgets/vehicle_pod.dart';
import '../../shared/widgets/car_top_view.dart';
import '../../shared/widgets/floating_nav_bar.dart';
import 'settings_tab.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _navIndex = 0;

  @override
  Widget build(BuildContext context) {
    final colors = context.appColors;

    return Scaffold(
      backgroundColor: colors.scaffoldBg,
      body: IndexedStack(
        index: _navIndex,
        children: [
          const _DashboardTab(),
          Center(child: Text('Battery',
              style: TextStyle(color: colors.textPrimary))),
          Center(child: Text('Parking',
              style: TextStyle(color: colors.textPrimary))),
          Center(child: Text('Audio',
              style: TextStyle(color: colors.textPrimary))),
          const SettingsTab(),
        ],
      ),
      bottomNavigationBar: FloatingNavBar(
        currentIndex: _navIndex,
        onTap: (i) => setState(() => _navIndex = i),
      ),
    );
  }
}

class _DashboardTab extends StatelessWidget {
  const _DashboardTab();

  @override
  Widget build(BuildContext context) {
    final colors = context.appColors;

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

                  // ── Header ─────────────────────────────────────
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Dashboard',
                            style: GoogleFonts.inter(
                              fontSize: 20,
                              fontWeight: FontWeight.w700,
                              color: colors.textPrimary,
                            ),
                          ),
                          Text(
                            'Live vehicle stats',
                            style: GoogleFonts.inter(
                              fontSize: 11,
                              fontWeight: FontWeight.w400,
                              color: colors.textSecondary,
                            ),
                          ),
                        ],
                      ),
                      // Glassmorphism notification bell
                      ClipRRect(
                        borderRadius: BorderRadius.circular(12),
                        child: BackdropFilter(
                          filter: ImageFilter.blur(sigmaX: 8, sigmaY: 8),
                          child: Container(
                            width: 36,
                            height: 36,
                            decoration: BoxDecoration(
                              color: colors.surface.withValues(alpha: 0.6),
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(
                                  color: colors.surface.withValues(alpha: 0.8),
                                  width: 1),
                              boxShadow: [
                                colors.neuShadow1,
                                colors.neuShadow2
                              ],
                            ),
                            child: Icon(Icons.notifications_outlined,
                                size: 17, color: colors.textSecondary),
                          ),
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 14),

                  // ── 3 Stat Cards ───────────────────────────────
                  Row(
                    children: [
                      SizedBox(
                        width: cardW,
                        child: StatCard(
                          label: 'Consumption',
                          value: '14',
                          unit: 'ep100',
                          tint: kCard1Gradient[0],
                          gradient: kCard1Gradient,
                        ),
                      ),
                      const SizedBox(width: 10),
                      SizedBox(
                        width: cardW,
                        child: StatCard(
                          label: 'Avg. speed',
                          value: '56.5',
                          unit: 'mps',
                          tint: kCard2Gradient[0],
                          gradient: kCard2Gradient,
                        ),
                      ),
                      const SizedBox(width: 10),
                      SizedBox(
                        width: cardW,
                        child: StatCard(
                          label: 'Consumption',
                          value: '06',
                          unit: 'ep100',
                          tint: kCard3Gradient[0],
                          gradient: kCard3Gradient,
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 16),

                  // ── Speedometer ─────────────────────────────────
                  const SpeedometerGauge(value: 56.5, max: 120),

                  const SizedBox(height: 6),

                  // ── Fuel row ────────────────────────────────────
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.local_gas_station,
                          size: 15, color: kFuelOrange),
                      const SizedBox(width: 5),
                      Text(
                        '200 ml',
                        style: GoogleFonts.inter(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: kFuelOrange,
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 16),

                  // ── Vehicle Status Row (pods + car) ─────────────
                  SizedBox(
                    height: 280,
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        // Left pod
                        Flexible(
                          flex: 1,
                          child: SizedBox(
                            height: 250,
                            child: VehiclePod(
                              headerIcon: Icons.light_outlined,
                              topIcon: Icons.light_outlined,
                              topValue: '0',
                              topStatus: '0°F  100%',
                              middleIcon: Icons.thermostat_outlined,
                              middleValue: '0°F',
                              middleStatus: '100%',
                              bottomIcon: Icons.local_gas_station,
                              bottomValue: '25 L',
                              bottomColor: kGood,
                              alignRight: false,
                            ),
                          ),
                        ),

                        const SizedBox(width: 8),

                        // Center car
                        const SizedBox(
                          width: 170,
                          child: CarTopView(timeMin: 56, distanceMi: 56),
                        ),

                        const SizedBox(width: 8),

                        // Right pod
                        Flexible(
                          flex: 1,
                          child: SizedBox(
                            height: 250,
                            child: VehiclePod(
                              headerIcon: Icons.directions_car_outlined,
                              topIcon: Icons.directions_car_outlined,
                              topValue: '0',
                              topStatus: '0°F  100%',
                              middleIcon: Icons.thermostat_outlined,
                              middleValue: '0°F',
                              middleStatus: '100%',
                              bottomIcon:
                                  Icons.battery_charging_full_outlined,
                              bottomValue: '40%',
                              bottomColor: kGood,
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
}
