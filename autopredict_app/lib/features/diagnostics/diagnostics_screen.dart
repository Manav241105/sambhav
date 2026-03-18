import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/typography.dart';
import '../../core/models/diagnostic_component.dart';
import '../../core/providers/diagnostics_provider.dart';

class DiagnosticsScreen extends ConsumerWidget {
  const DiagnosticsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.appColors;
    final diagnosticsAsync = ref.watch(diagnosticsProvider);

    return Scaffold(
      backgroundColor: colors.scaffoldBg,
      appBar: AppBar(
        backgroundColor: colors.scaffoldBg, elevation: 0,
        title: Text('Diagnostics', style: kTitle(color: colors.textPrimary)),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: colors.textSecondary),
            onPressed: () => ref.invalidate(diagnosticsProvider),
          ),
        ],
      ),
      body: diagnosticsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator(color: kAccent)),
        error: (e, _) => Center(child: Text('Failed to load: $e')),
        data: (components) => _Body(components: components, colors: colors),
      ),
    );
  }
}

class _Body extends StatelessWidget {
  final List<DiagnosticComponent> components;
  final dynamic colors;
  const _Body({required this.components, required this.colors});

  @override
  Widget build(BuildContext context) {
    final overall = components.map((c) => c.healthPct).reduce((a, b) => a + b) / components.length;
    final criticalCount = components.where((c) => c.status == ComponentStatus.critical).length;
    final warningCount = components.where((c) => c.status == ComponentStatus.warning).length;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(children: [
        // Overall health bar
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: colors.surface,
            borderRadius: BorderRadius.circular(rLG),
            boxShadow: [colors.cardShadowStyle],
          ),
          child: Column(children: [
            Row(children: [
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('Overall Health', style: kLabel(color: colors.textSecondary)),
                const SizedBox(height: 8),
                ClipRRect(
                  borderRadius: BorderRadius.circular(rFull),
                  child: LinearProgressIndicator(
                    value: overall / 100,
                    minHeight: 10,
                    backgroundColor: colors.neuBg,
                    valueColor: AlwaysStoppedAnimation(
                      overall > 70 ? kGood : overall > 45 ? kWarning : kDanger,
                    ),
                  ),
                ),
              ])),
              const SizedBox(width: 16),
              Text('${overall.toStringAsFixed(0)}%',
                  style: kTitle(color: overall > 70 ? kGood : overall > 45 ? kWarning : kDanger)),
            ]),
            const SizedBox(height: 12),
            Row(children: [
              _StatusBadge(count: criticalCount, label: 'Critical', color: kDanger),
              const SizedBox(width: 12),
              _StatusBadge(count: warningCount, label: 'Warning', color: kWarning),
              const SizedBox(width: 12),
              _StatusBadge(
                count: components.length - criticalCount - warningCount,
                label: 'Good', color: kGood,
              ),
            ]),
          ]),
        ),
        const SizedBox(height: 12),

        // Component grid
        Expanded(
          child: ListView.separated(
            padding: const EdgeInsets.only(bottom: 80),
            itemCount: components.length,
            separatorBuilder: (_, __) => const SizedBox(height: 12),
            itemBuilder: (context, i) => _ComponentCard(data: components[i], colors: colors),
          ),
        ),
      ]),
    );
  }
}

class _ComponentCard extends StatelessWidget {
  final DiagnosticComponent data;
  final dynamic colors;
  const _ComponentCard({required this.data, required this.colors});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => _showDetails(context, data, colors),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: colors.surface,
          borderRadius: BorderRadius.circular(rLG),
          boxShadow: [colors.cardShadowStyle],
          border: data.status == ComponentStatus.critical
              ? Border.all(color: kDanger.withValues(alpha: 0.3))
              : null,
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Icon(data.icon, size: 18, color: data.statusColor),
            const SizedBox(width: 8),
            Expanded(child: Text(data.name,
                style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w600,
                    color: colors.textPrimary))),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: data.statusColor.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(rFull),
              ),
              child: Text(data.statusLabel,
                  style: GoogleFonts.inter(fontSize: 10, fontWeight: FontWeight.w700,
                      color: data.statusColor)),
            ),
          ]),
          const SizedBox(height: 10),
          Row(children: [
            Text('${data.reading} ${data.unit}',
                style: GoogleFonts.inter(fontSize: 22, fontWeight: FontWeight.w800,
                    color: colors.textPrimary)),
            const Spacer(),
            if (data.daysToFailure != null) ...[
              Icon(Icons.schedule, size: 13, color: data.statusColor),
              const SizedBox(width: 4),
              Text('~${data.daysToFailure}d',
                  style: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w600,
                      color: data.statusColor)),
            ],
          ]),
          const SizedBox(height: 8),
          // Mini trend
          if (data.history30d.isNotEmpty)
            SizedBox(
              height: 36,
              child: _MiniTrend(data: data.history30d, color: data.statusColor),
            ),
          const SizedBox(height: 6),
          Text(data.prediction,
              style: GoogleFonts.inter(fontSize: 11, color: colors.textSecondary)),
        ]),
      ),
    );
  }

  void _showDetails(BuildContext context, DiagnosticComponent data, colors) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: colors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(rLG)),
      ),
      builder: (_) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(
            width: 40, height: 4,
            margin: const EdgeInsets.only(bottom: 16),
            decoration: BoxDecoration(
              color: colors.gaugeTrackColor, borderRadius: BorderRadius.circular(2),
            ),
          ),
          Row(children: [
            Icon(data.icon, size: 24, color: data.statusColor),
            const SizedBox(width: 12),
            Text(data.name, style: GoogleFonts.inter(
              fontSize: 20, fontWeight: FontWeight.w700, color: colors.textPrimary,
            )),
          ]),
          const SizedBox(height: 16),
          _DetailRow('Reading', '${data.reading} ${data.unit}', colors),
          _DetailRow('Health', '${data.healthPct.toStringAsFixed(0)}%', colors),
          _DetailRow('Prediction', data.prediction, colors),
          _DetailRow('Recommendation', data.recommendation, colors),
          if (data.dtcCode != null) _DetailRow('DTC Code', data.dtcCode!, colors),
          if (data.costEstimate > 0)
            _DetailRow('Est. Cost', '₹${data.costEstimate.toStringAsFixed(0)}', colors),
          const SizedBox(height: 20),
          if (data.status != ComponentStatus.good)
            GestureDetector(
              onTap: () { Navigator.pop(context); context.push('/book-new'); },
              child: Container(
                width: double.infinity, height: 48,
                decoration: BoxDecoration(color: kAccent, borderRadius: BorderRadius.circular(rMD)),
                child: Center(child: Text('Book Service for ${data.name}',
                    style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w700, color: kDark))),
              ),
            ),
          const SizedBox(height: 24),
        ]),
      ),
    );
  }

  Widget _DetailRow(String label, String value, colors) => Padding(
    padding: const EdgeInsets.only(bottom: 10),
    child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      SizedBox(width: 120, child: Text(label,
          style: GoogleFonts.inter(fontSize: 13, color: colors.textSecondary))),
      Expanded(child: Text(value,
          style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w600,
              color: colors.textPrimary))),
    ]),
  );
}

class _MiniTrend extends StatelessWidget {
  final List<double> data;
  final Color color;
  const _MiniTrend({required this.data, required this.color});

  @override
  Widget build(BuildContext context) => LineChart(
    LineChartData(
      gridData: const FlGridData(show: false),
      titlesData: const FlTitlesData(show: false),
      borderData: FlBorderData(show: false),
      lineBarsData: [LineChartBarData(
        spots: data.asMap().entries.map((e) => FlSpot(e.key.toDouble(), e.value)).toList(),
        isCurved: true, color: color, barWidth: 1.5,
        dotData: const FlDotData(show: false),
        belowBarData: BarAreaData(show: true, color: color.withValues(alpha: 0.08)),
      )],
    ),
  );
}

class _StatusBadge extends StatelessWidget {
  final int count;
  final String label;
  final Color color;
  const _StatusBadge({required this.count, required this.label, required this.color});

  @override
  Widget build(BuildContext context) => Row(children: [
    Container(
      width: 8, height: 8,
      decoration: BoxDecoration(color: color, shape: BoxShape.circle),
    ),
    const SizedBox(width: 5),
    Text('$count $label', style: GoogleFonts.inter(fontSize: 12, color: color, fontWeight: FontWeight.w600)),
  ]);
}
