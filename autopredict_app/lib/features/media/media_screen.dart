import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/colors.dart';
import '../../core/providers/vehicle_provider.dart';

class MediaScreen extends ConsumerWidget {
  const MediaScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final vehicle = ref.watch(vehicleProvider);
    final colors = context.appColors;
    final speed = vehicle.speedMph;

    // Simulate noise level based on speed
    final noiseDb = (45 + speed * 0.5).clamp(40.0, 90.0);
    final noiseLabel = noiseDb < 55 ? 'Quiet' : noiseDb < 70 ? 'Moderate' : 'Loud';
    final noiseColor = noiseDb < 55 ? kGood : noiseDb < 70 ? kWarning : kDanger;

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
                Text('Media & Cabin', style: GoogleFonts.inter(
                  fontSize: 22, fontWeight: FontWeight.w700, color: colors.textPrimary,
                )),
                Text('Road noise & comfort', style: GoogleFonts.inter(
                  fontSize: 12, color: colors.textSecondary,
                )),
                const SizedBox(height: 24),

                // Noise meter card
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: colors.surface,
                    borderRadius: BorderRadius.circular(rLG),
                    boxShadow: [colors.cardShadowStyle],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(children: [
                        Icon(Icons.graphic_eq, size: 18, color: noiseColor),
                        const SizedBox(width: 8),
                        Text('Road Noise Level', style: GoogleFonts.inter(
                          fontSize: 14, fontWeight: FontWeight.w600, color: colors.textPrimary,
                        )),
                        const Spacer(),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: noiseColor.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(rFull),
                          ),
                          child: Text(noiseLabel, style: GoogleFonts.inter(
                            fontSize: 11, fontWeight: FontWeight.w600, color: noiseColor,
                          )),
                        ),
                      ]),
                      const SizedBox(height: 16),
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text('${noiseDb.toStringAsFixed(0)}',
                              style: GoogleFonts.inter(
                                fontSize: 52, fontWeight: FontWeight.w800, color: colors.textPrimary, height: 1,
                              )),
                          Padding(
                            padding: const EdgeInsets.only(bottom: 8),
                            child: Text(' dB', style: GoogleFonts.inter(
                              fontSize: 18, color: colors.textSecondary,
                            )),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(rFull),
                        child: LinearProgressIndicator(
                          value: (noiseDb - 40) / 50,
                          minHeight: 8,
                          backgroundColor: colors.gaugeTrackColor,
                          valueColor: AlwaysStoppedAnimation(noiseColor),
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 16),

                // Cabin comfort stats
                Row(children: [
                  _ComfortTile(icon: Icons.thermostat, label: 'Cabin Temp',
                      value: '24°C', color: kWarning, colors: colors),
                  const SizedBox(width: 12),
                  _ComfortTile(icon: Icons.water_drop_outlined, label: 'Humidity',
                      value: '62%', color: const Color(0xFF38BDF8), colors: colors),
                  const SizedBox(width: 12),
                  _ComfortTile(icon: Icons.air, label: 'Air Quality',
                      value: 'Good', color: kGood, colors: colors),
                ]),

                const SizedBox(height: 24),

                // Voice command section
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [kAccent.withValues(alpha: 0.15), kAccentDark.withValues(alpha: 0.08)],
                    ),
                    borderRadius: BorderRadius.circular(rLG),
                    border: Border.all(color: kAccent.withValues(alpha: 0.3)),
                  ),
                  child: Row(children: [
                    Container(
                      width: 52, height: 52,
                      decoration: const BoxDecoration(
                        color: kAccent,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.mic, size: 24, color: Colors.black),
                    ),
                    const SizedBox(width: 16),
                    Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text('Voice Commands', style: GoogleFonts.inter(
                        fontSize: 15, fontWeight: FontWeight.w700, color: colors.textPrimary,
                      )),
                      Text('"Hey AutoPredict, how are my brakes?"',
                          style: GoogleFonts.inter(fontSize: 12, color: colors.textSecondary)),
                    ]),
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
}

class _ComfortTile extends StatelessWidget {
  final IconData icon;
  final String label, value;
  final Color color;
  final dynamic colors;
  const _ComfortTile({required this.icon, required this.label, required this.value,
    required this.color, required this.colors});

  @override
  Widget build(BuildContext context) => Expanded(
    child: Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(rMD),
        boxShadow: [colors.cardShadowStyle],
      ),
      child: Column(children: [
        Icon(icon, size: 20, color: color),
        const SizedBox(height: 6),
        Text(value, style: GoogleFonts.inter(
          fontSize: 14, fontWeight: FontWeight.w700, color: colors.textPrimary,
        )),
        Text(label, style: GoogleFonts.inter(fontSize: 10, color: colors.textSecondary)),
      ]),
    ),
  );
}
