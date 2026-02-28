import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/typography.dart';
import '../../shared/widgets/stat_card.dart';
import '../../shared/widgets/speedometer_gauge.dart';
import '../../shared/widgets/vehicle_pod.dart';
import '../../shared/widgets/car_top_view.dart';
import '../../shared/widgets/floating_nav_bar.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _navIndex = 0;
  double _speed = 56.5;

  final List<Widget> _tabs = [];

  @override
  void initState() {
    super.initState();
    _tabs.addAll([
      const _DashboardTab(),
      const Center(child: Text('Documents')),
      const Center(child: Text('Vehicle')),
      const Center(child: Text('Music')),
      const Center(child: Text('Settings')),
    ]);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      body: _tabs[_navIndex],
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
    return SafeArea(
      child: SingleChildScrollView(
        physics: const BouncingScrollPhysics(),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Column(
            children: [
              // ── 3 Stat Cards ──────────────────────────────
              Row(
                children: [
                  Expanded(child: StatCard(label: 'Consumption', value: '14', unit: 'ep/100', tint: kCardBlue)),
                  const SizedBox(width: 8),
                  Expanded(child: StatCard(label: 'Avg. speed', value: '56.5', unit: 'mps', tint: kCardYellow)),
                  const SizedBox(width: 8),
                  Expanded(child: StatCard(label: 'Consumption', value: '06', unit: 'ep/100', tint: kCardGreen)),
                ],
              ),
              const SizedBox(height: 24),

              // ── Speedometer Gauge ─────────────────────────
              SpeedometerGauge(value: 56.5, max: 120),
              const SizedBox(height: 6),

              // ── Fuel row ──────────────────────────────────
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.local_gas_station, size: 16, color: Color(0xFF6B7280)),
                  const SizedBox(width: 6),
                  Text('200 ml', style: kCaption()),
                ],
              ),
              const SizedBox(height: 24),

              // ── Vehicle Status (2 pods + car) ─────────────
              SizedBox(
                height: 260,
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Left pod
                    Expanded(
                      child: VehiclePod(
                        topIcon: Icons.tire_repair,
                        topValue: '0',
                        topStatus: '0°F  100%',
                        bottomIcon: Icons.local_gas_station,
                        bottomValue: '25 L',
                        bottomColor: kFuelOrange,
                        headerIcon: Icons.volume_up_outlined,
                      ),
                    ),
                    const SizedBox(width: 12),

                    // Center car
                    const CarTopView(timeMin: 56, distanceMi: 56),

                    const SizedBox(width: 12),

                    // Right pod
                    Expanded(
                      child: VehiclePod(
                        topIcon: Icons.lock_outline,
                        topValue: '0',
                        topStatus: '0°F  100%',
                        bottomIcon: Icons.thermostat_outlined,
                        bottomValue: '40%',
                        bottomColor: kTempYellow,
                        headerIcon: Icons.directions_car_outlined,
                        alignRight: true,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 100), // nav bar clearance
            ],
          ),
        ),
      ),
    );
  }
}
