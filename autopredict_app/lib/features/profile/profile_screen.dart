import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/colors.dart';
import '../../core/providers/vehicle_provider.dart';
import '../../core/providers/diagnostics_provider.dart';
import '../../core/models/diagnostic_component.dart';
import '../../core/theme/theme_provider.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.appColors;
    final diagnosticsAsync = ref.watch(diagnosticsProvider);
    final themeMode = ref.watch(themeModeProvider);
    final isDark = themeMode == ThemeMode.dark;

    final driverScore = ref.watch(driverScoreProvider);

    return Scaffold(
      backgroundColor: colors.scaffoldBg,
      body: SafeArea(
        child: SingleChildScrollView(
          physics: const BouncingScrollPhysics(),
          child: Column(children: [
            // Profile header
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: colors.surface,
                boxShadow: [colors.cardShadowStyle],
              ),
              child: Column(children: [
                Stack(alignment: Alignment.bottomRight, children: [
                  Container(
                    width: 80, height: 80,
                    decoration: const BoxDecoration(
                      color: kAccent,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.person, size: 40, color: Colors.black),
                  ),
                  Container(
                    width: 24, height: 24,
                    decoration: const BoxDecoration(
                      color: kGood, shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.check, size: 14, color: Colors.white),
                  ),
                ]),
                const SizedBox(height: 12),
                Text('Manav Parekh', style: GoogleFonts.inter(
                  fontSize: 20, fontWeight: FontWeight.w700, color: colors.textPrimary,
                )),
                Text('manav@autopredict.in', style: GoogleFonts.inter(
                  fontSize: 13, color: colors.textSecondary,
                )),
                const SizedBox(height: 16),
                // Stats row
                Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [
                  _StatItem('Driver Score', '${driverScore.toInt()}', colors),
                  Container(width: 1, height: 36, color: colors.gaugeTrackColor),
                  _StatItem('Trips', '142', colors),
                  Container(width: 1, height: 36, color: colors.gaugeTrackColor),
                  _StatItem('km Driven', '12,480', colors),
                ]),
              ]),
            ),

            const SizedBox(height: 16),

            // Vehicle card
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: colors.surface,
                  borderRadius: BorderRadius.circular(rLG),
                  boxShadow: [colors.cardShadowStyle],
                ),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Row(children: [
                    const Icon(Icons.directions_car, size: 18, color: kAccentDark),
                    const SizedBox(width: 8),
                    Text('My Vehicle', style: GoogleFonts.inter(
                      fontSize: 14, fontWeight: FontWeight.w700, color: colors.textPrimary,
                    )),
                  ]),
                  const Divider(height: 20),
                  _ProfileRow('Make & Model', 'Toyota Camry 2021', colors),
                  _ProfileRow('VIN', 'JT2BF22KXY0123456', colors),
                  _ProfileRow('Reg. No.', 'MH 01 AB 1234', colors),
                  _ProfileRow('Fuel Type', 'Petrol', colors),
                  _ProfileRow('Odometer', '12,480 km', colors),
                ]),
              ),
            ),

            const SizedBox(height: 12),

            // Diagnostics summary
            diagnosticsAsync.when(
              data: (components) {
                final critical = components.where((c) => c.status == ComponentStatus.critical).length;
                return Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: critical > 0
                          ? kDanger.withValues(alpha: 0.06)
                          : colors.surface,
                      borderRadius: BorderRadius.circular(rLG),
                      border: Border.all(
                        color: critical > 0
                            ? kDanger.withValues(alpha: 0.3)
                            : Colors.transparent,
                      ),
                      boxShadow: [colors.cardShadowStyle],
                    ),
                    child: Row(children: [
                      Icon(
                        critical > 0 ? Icons.warning_amber_rounded : Icons.check_circle_outline,
                        color: critical > 0 ? kDanger : kGood, size: 24,
                      ),
                      const SizedBox(width: 12),
                      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(
                          critical > 0
                              ? '$critical Critical Issue${critical > 1 ? 's' : ''} Found'
                              : 'All Systems Good',
                          style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w700,
                              color: critical > 0 ? kDanger : kGood),
                        ),
                        Text(
                          critical > 0 ? 'Service required immediately' : 'Last checked just now',
                          style: GoogleFonts.inter(fontSize: 12, color: colors.textSecondary),
                        ),
                      ])),
                    ]),
                  ),
                );
              },
              loading: () => const SizedBox.shrink(),
              error: (_, __) => const SizedBox.shrink(),
            ),

            const SizedBox(height: 12),

            // Settings
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Container(
                decoration: BoxDecoration(
                  color: colors.surface,
                  borderRadius: BorderRadius.circular(rLG),
                  boxShadow: [colors.cardShadowStyle],
                ),
                child: Column(children: [
                  _SettingTile(
                    icon: isDark ? Icons.dark_mode : Icons.light_mode,
                    label: isDark ? 'Dark Mode' : 'Light Mode',
                    trailing: Switch(
                      value: isDark,
                      activeColor: kAccent,
                      // setMode also persists the choice.
                      onChanged: (v) => ref.read(themeModeProvider.notifier).setMode(v ? ThemeMode.dark : ThemeMode.light),
                    ),
                    colors: colors,
                  ),
                  _Divider(colors: colors),
                  _SettingTile(icon: Icons.notifications_outlined, label: 'Notifications', colors: colors),
                  _Divider(colors: colors),
                  _SettingTile(icon: Icons.security_outlined, label: 'Privacy', colors: colors),
                  _Divider(colors: colors),
                  _SettingTile(icon: Icons.info_outline, label: 'About · v1.0.0', colors: colors),
                ]),
              ),
            ),

            const SizedBox(height: 80),
          ]),
        ),
      ),
    );
  }
}

class _StatItem extends StatelessWidget {
  final String label, value;
  final dynamic colors;
  const _StatItem(this.label, this.value, this.colors);

  @override
  Widget build(BuildContext context) => Column(children: [
    Text(value, style: GoogleFonts.inter(
      fontSize: 20, fontWeight: FontWeight.w800, color: colors.textPrimary,
    )),
    Text(label, style: GoogleFonts.inter(fontSize: 11, color: colors.textSecondary)),
  ]);
}

class _ProfileRow extends StatelessWidget {
  final String label, value;
  final dynamic colors;
  const _ProfileRow(this.label, this.value, this.colors);

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 8),
    child: Row(children: [
      SizedBox(width: 110, child: Text(label, style: GoogleFonts.inter(
        fontSize: 12, color: colors.textSecondary,
      ))),
      Expanded(child: Text(value, style: GoogleFonts.inter(
        fontSize: 12, fontWeight: FontWeight.w600, color: colors.textPrimary,
      ))),
    ]),
  );
}

class _SettingTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final Widget? trailing;
  final dynamic colors;
  const _SettingTile({required this.icon, required this.label, required this.colors, this.trailing});

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    child: Row(children: [
      Icon(icon, size: 20, color: colors.textSecondary),
      const SizedBox(width: 14),
      Expanded(child: Text(label, style: GoogleFonts.inter(
        fontSize: 14, color: colors.textPrimary,
      ))),
      trailing ?? Icon(Icons.chevron_right, size: 18, color: colors.textSecondary),
    ]),
  );
}

class _Divider extends StatelessWidget {
  final dynamic colors;
  const _Divider({required this.colors});

  @override
  Widget build(BuildContext context) => Divider(
    height: 1, indent: 50, endIndent: 16,
    color: colors.navBorder,
  );
}
