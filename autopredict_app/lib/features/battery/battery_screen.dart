import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/colors.dart';
import '../../core/providers/vehicle_provider.dart';

class BatteryScreen extends ConsumerWidget {
  const BatteryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final vehicle = ref.watch(vehicleProvider);
    final colors = context.appColors;
    final voltage = vehicle.batteryVoltage;
    final pct = ((voltage - 11.0) / (14.4 - 11.0) * 100).clamp(0.0, 100.0);

    return Scaffold(
      backgroundColor: colors.scaffoldBg,
      body: SafeArea(
        child: SingleChildScrollView(
          physics: const BouncingScrollPhysics(),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header
                Text('Battery', style: GoogleFonts.inter(
                  fontSize: 22, fontWeight: FontWeight.w700, color: colors.textPrimary,
                )),
                Text('Live power system health', style: GoogleFonts.inter(
                  fontSize: 12, color: colors.textSecondary,
                )),
                const SizedBox(height: 24),

                // Big circular battery gauge
                Center(
                  child: SizedBox(
                    width: 200, height: 200,
                    child: Stack(
                      alignment: Alignment.center,
                      children: [
                        SizedBox(
                          width: 200, height: 200,
                          child: CircularProgressIndicator(
                            value: pct / 100,
                            strokeWidth: 14,
                            backgroundColor: colors.gaugeTrackColor,
                            valueColor: AlwaysStoppedAnimation(_batteryColor(pct)),
                            strokeCap: StrokeCap.round,
                          ),
                        ),
                        Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.bolt, size: 28, color: _batteryColor(pct)),
                            Text('${pct.toStringAsFixed(0)}%',
                                style: GoogleFonts.inter(
                                  fontSize: 40, fontWeight: FontWeight.w800,
                                  color: colors.textPrimary,
                                )),
                            Text('${voltage.toStringAsFixed(2)}V',
                                style: GoogleFonts.inter(
                                  fontSize: 14, color: colors.textSecondary,
                                )),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 24),

                // Stat row
                Row(children: [
                  _StatTile(label: 'Voltage', value: '${voltage.toStringAsFixed(2)}V', colors: colors),
                  const SizedBox(width: 12),
                  _StatTile(label: 'Status',
                    value: voltage > 13.0 ? 'Charging' : voltage > 12.4 ? 'Good' : 'Weak',
                    colors: colors),
                  const SizedBox(width: 12),
                  _StatTile(label: 'Est. Range', value: '${(pct * 3.2).toStringAsFixed(0)} km', colors: colors),
                ]),

                const SizedBox(height: 24),

                // Charge curve chart
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: colors.surface,
                    borderRadius: BorderRadius.circular(rLG),
                    boxShadow: [colors.cardShadowStyle],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Voltage Trend (Today)',
                          style: GoogleFonts.inter(
                            fontSize: 14, fontWeight: FontWeight.w600, color: colors.textPrimary,
                          )),
                      const SizedBox(height: 16),
                      SizedBox(
                        height: 140,
                        child: LineChart(
                          LineChartData(
                            gridData: FlGridData(
                              drawVerticalLine: false,
                              getDrawingHorizontalLine: (_) => FlLine(
                                color: colors.gaugeTrackColor, strokeWidth: 1,
                              ),
                            ),
                            titlesData: FlTitlesData(
                              leftTitles: AxisTitles(sideTitles: SideTitles(
                                showTitles: true, reservedSize: 36,
                                getTitlesWidget: (v, _) => Text(v.toStringAsFixed(1),
                                    style: GoogleFonts.inter(fontSize: 9, color: colors.textSecondary)),
                              )),
                              bottomTitles: AxisTitles(sideTitles: SideTitles(
                                showTitles: true, interval: 3,
                                getTitlesWidget: (v, _) => Text('${v.toInt()}h',
                                    style: GoogleFonts.inter(fontSize: 9, color: colors.textSecondary)),
                              )),
                              topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                              rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                            ),
                            borderData: FlBorderData(show: false),
                            minY: 11.0, maxY: 14.5,
                            lineBarsData: [
                              LineChartBarData(
                                spots: _voltageSpots(voltage),
                                isCurved: true,
                                color: kAccent,
                                barWidth: 2.5,
                                dotData: const FlDotData(show: false),
                                belowBarData: BarAreaData(
                                  show: true,
                                  color: kAccent.withValues(alpha: 0.08),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 16),

                // AI Tip card
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: kAccent.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(rLG),
                    border: Border.all(color: kAccent.withValues(alpha: 0.3)),
                  ),
                  child: Row(children: [
                    const Icon(Icons.lightbulb_outline, color: kAccentDark, size: 20),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        voltage < 12.0
                            ? '⚠️ Battery voltage is critically low. Consider a battery health test.'
                            : 'Tip: Avoid draining battery below 12V to maximise lifespan.',
                        style: GoogleFonts.inter(fontSize: 13, color: kAccentDark),
                      ),
                    ),
                  ]),
                ),

                const SizedBox(height: 80),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Color _batteryColor(double pct) {
    if (pct > 60) return kGood;
    if (pct > 30) return kWarning;
    return kDanger;
  }

  List<FlSpot> _voltageSpots(double current) {
    final base = [12.6, 12.5, 12.4, 13.8, 14.2, 13.9, 13.5, 13.0, 12.8, 12.7, current];
    return base.asMap().entries
        .map((e) => FlSpot(e.key.toDouble(), e.value))
        .toList();
  }
}

class _StatTile extends StatelessWidget {
  final String label, value;
  final dynamic colors;
  const _StatTile({required this.label, required this.value, required this.colors});

  @override
  Widget build(BuildContext context) => Expanded(
    child: Container(
      padding: const EdgeInsets.symmetric(vertical: 14),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(rMD),
        boxShadow: [colors.cardShadowStyle],
      ),
      child: Column(children: [
        Text(value, style: GoogleFonts.inter(
          fontSize: 16, fontWeight: FontWeight.w700, color: colors.textPrimary,
        )),
        const SizedBox(height: 2),
        Text(label, style: GoogleFonts.inter(fontSize: 11, color: colors.textSecondary)),
      ]),
    ),
  );
}
