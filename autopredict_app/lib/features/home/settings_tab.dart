import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/theme_provider.dart';
import '../../core/theme/colors.dart';

class SettingsTab extends ConsumerWidget {
  const SettingsTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentMode = ref.watch(themeModeProvider);
    final colors = context.appColors;

    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        children: [
          const SizedBox(height: 4),
          Text(
            'Settings',
            style: GoogleFonts.inter(
              fontSize: 20,
              fontWeight: FontWeight.w700,
              color: colors.textPrimary,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Customize your experience',
            style: GoogleFonts.inter(
              fontSize: 11,
              fontWeight: FontWeight.w400,
              color: colors.textSecondary,
            ),
          ),
          const SizedBox(height: 24),

          // ── Quick Dark Mode Toggle ──────────────────────────────
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: colors.surface,
              borderRadius: BorderRadius.circular(rMD),
              boxShadow: [colors.cardShadowStyle],
            ),
            child: Row(
              children: [
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: currentMode == ThemeMode.dark
                        ? kAccent.withValues(alpha: 0.2)
                        : colors.neuBg,
                    borderRadius: BorderRadius.circular(rSM),
                  ),
                  child: Icon(
                    currentMode == ThemeMode.dark
                        ? Icons.dark_mode
                        : Icons.light_mode,
                    size: 20,
                    color: currentMode == ThemeMode.dark
                        ? kAccentDark
                        : colors.textSecondary,
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Dark Mode',
                        style: GoogleFonts.inter(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: colors.textPrimary,
                        ),
                      ),
                      Text(
                        currentMode == ThemeMode.dark
                            ? 'On'
                            : currentMode == ThemeMode.light
                                ? 'Off'
                                : 'Following system',
                        style: GoogleFonts.inter(
                          fontSize: 11,
                          fontWeight: FontWeight.w400,
                          color: colors.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
                Switch(
                  value: currentMode == ThemeMode.dark,
                  activeThumbColor: kAccent,
                  activeTrackColor: kAccent.withValues(alpha: 0.3),
                  inactiveThumbColor: colors.textSecondary,
                  inactiveTrackColor: colors.neuBg,
                  onChanged: (dark) {
                    ref.read(themeModeProvider.notifier).setMode(
                          dark ? ThemeMode.dark : ThemeMode.light,
                        );
                  },
                ),
              ],
            ),
          ),

          const SizedBox(height: 24),

          // ── Appearance Section ──────────────────────────────────────
          _SectionHeader(title: 'APPEARANCE', colors: colors),
          const SizedBox(height: 10),
          _ThemeTile(
            icon: Icons.light_mode_outlined,
            label: 'Light',
            subtitle: 'Classic bright look',
            isSelected: currentMode == ThemeMode.light,
            colors: colors,
            onTap: () =>
                ref.read(themeModeProvider.notifier).setMode(ThemeMode.light),
          ),
          const SizedBox(height: 8),
          _ThemeTile(
            icon: Icons.dark_mode_outlined,
            label: 'Dark',
            subtitle: 'Easy on the eyes',
            isSelected: currentMode == ThemeMode.dark,
            colors: colors,
            onTap: () =>
                ref.read(themeModeProvider.notifier).setMode(ThemeMode.dark),
          ),
          const SizedBox(height: 8),
          _ThemeTile(
            icon: Icons.settings_suggest_outlined,
            label: 'System',
            subtitle: 'Follow device setting',
            isSelected: currentMode == ThemeMode.system,
            colors: colors,
            onTap: () =>
                ref.read(themeModeProvider.notifier).setMode(ThemeMode.system),
          ),

          const SizedBox(height: 28),

          // ── General Section ─────────────────────────────────────────
          _SectionHeader(title: 'GENERAL', colors: colors),
          const SizedBox(height: 10),
          ...[
            ('Notification Preferences', Icons.notifications_outlined),
            ('Language', Icons.language),
            ('Units & Measurements', Icons.straighten_outlined),
          ].map((e) => _SettingsTile(
                icon: e.$2,
                label: e.$1,
                colors: colors,
              )),

          const SizedBox(height: 28),

          // ── Support Section ─────────────────────────────────────────
          _SectionHeader(title: 'SUPPORT', colors: colors),
          const SizedBox(height: 10),
          ...[
            ('Contact Support', Icons.headset_mic_outlined),
            ('Privacy Policy', Icons.shield_outlined),
            ('About', Icons.info_outline),
          ].map((e) => _SettingsTile(
                icon: e.$2,
                label: e.$1,
                colors: colors,
              )),

          const SizedBox(height: 28),

          // ── Version ─────────────────────────────────────────────────
          Center(
            child: Text(
              'AutoPredict v1.0.0',
              style: GoogleFonts.inter(
                fontSize: 11,
                fontWeight: FontWeight.w400,
                color: colors.textSecondary,
              ),
            ),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}

// ── Section Header ──────────────────────────────────────────────────────────
class _SectionHeader extends StatelessWidget {
  final String title;
  final AppColors colors;
  const _SectionHeader({required this.title, required this.colors});

  @override
  Widget build(BuildContext context) {
    return Text(
      title,
      style: GoogleFonts.inter(
        fontSize: 12,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.4,
        color: colors.textSecondary,
      ),
    );
  }
}

// ── Theme Selection Tile ────────────────────────────────────────────────────
class _ThemeTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String subtitle;
  final bool isSelected;
  final AppColors colors;
  final VoidCallback onTap;

  const _ThemeTile({
    required this.icon,
    required this.label,
    required this.subtitle,
    required this.isSelected,
    required this.colors,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 250),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: isSelected
              ? kAccent.withValues(alpha: 0.12)
              : colors.surface,
          borderRadius: BorderRadius.circular(rMD),
          border: Border.all(
            color: isSelected ? kAccent : Colors.transparent,
            width: 1.5,
          ),
          boxShadow: [colors.cardShadowStyle],
        ),
        child: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: isSelected
                    ? kAccent.withValues(alpha: 0.2)
                    : colors.neuBg,
                borderRadius: BorderRadius.circular(rSM),
              ),
              child: Icon(icon,
                  size: 20,
                  color: isSelected ? kAccentDark : colors.textSecondary),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: GoogleFonts.inter(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: colors.textPrimary,
                    ),
                  ),
                  Text(
                    subtitle,
                    style: GoogleFonts.inter(
                      fontSize: 11,
                      fontWeight: FontWeight.w400,
                      color: colors.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
            if (isSelected)
              Container(
                width: 22,
                height: 22,
                decoration: const BoxDecoration(
                  color: kAccent,
                  shape: BoxShape.circle,
                ),
                child:
                    const Icon(Icons.check, size: 14, color: Colors.black87),
              ),
          ],
        ),
      ),
    );
  }
}

// ── General Settings Tile ───────────────────────────────────────────────────
class _SettingsTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final AppColors colors;

  const _SettingsTile({
    required this.icon,
    required this.label,
    required this.colors,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(rMD),
        boxShadow: [colors.cardShadowStyle],
      ),
      child: ListTile(
        leading: Icon(icon, size: 20, color: colors.textSecondary),
        title: Text(
          label,
          style: GoogleFonts.inter(
            fontSize: 14,
            fontWeight: FontWeight.w400,
            color: colors.textPrimary,
          ),
        ),
        trailing: Icon(Icons.chevron_right,
            size: 18, color: colors.textSecondary),
        onTap: () {},
      ),
    );
  }
}
