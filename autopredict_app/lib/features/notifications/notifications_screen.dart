import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/colors.dart';

class NotificationsScreen extends StatelessWidget {
  const NotificationsScreen({super.key});

  static final _notifications = [
    _Notif(
      icon: Icons.warning_amber_rounded,
      color: kDanger,
      title: 'CRITICAL: Brake Pads',
      body: 'Pads at 2.1mm — below safe threshold. Book service now.',
      time: '2m ago',
      read: false,
    ),
    _Notif(
      icon: Icons.battery_3_bar,
      color: kWarning,
      title: 'Battery Health Warning',
      body: 'Voltage dropped to 11.8V. Consider a battery load test.',
      time: '1h ago',
      read: false,
    ),
    _Notif(
      icon: Icons.calendar_today_outlined,
      color: kGood,
      title: 'Booking Confirmed',
      body: 'Brake Pads service — Tomorrow 10:00 AM · Bay A · Rajesh Kumar',
      time: '3h ago',
      read: true,
    ),
    _Notif(
      icon: Icons.tire_repair,
      color: kWarning,
      title: 'Low Tire Pressure',
      body: 'Front-left at 28 PSI. Recommended: 32 PSI.',
      time: '5h ago',
      read: true,
    ),
    _Notif(
      icon: Icons.psychology,
      color: const Color(0xFF38BDF8),
      title: 'AI Insight',
      body: 'Based on your driving the past 7 days, consider an oil change in ~800km.',
      time: '1d ago',
      read: true,
    ),
    _Notif(
      icon: Icons.local_gas_station,
      color: kFuelOrange,
      title: 'Fuel Reminder',
      body: 'Fuel level at 18%. Nearest station: 2.4km away.',
      time: '2d ago',
      read: true,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    final colors = context.appColors;

    return Scaffold(
      backgroundColor: colors.scaffoldBg,
      appBar: AppBar(
        backgroundColor: colors.scaffoldBg, elevation: 0,
        title: Text('Notifications', style: GoogleFonts.inter(
          fontSize: 20, fontWeight: FontWeight.w700, color: colors.textPrimary,
        )),
        actions: [
          TextButton(
            onPressed: () {},
            child: Text('Mark all read', style: GoogleFonts.inter(
              fontSize: 12, color: kAccentDark,
            )),
          ),
        ],
      ),
      body: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: _notifications.length,
        separatorBuilder: (_, __) => const SizedBox(height: 8),
        itemBuilder: (_, i) => _NotifCard(notif: _notifications[i], colors: colors),
      ),
    );
  }
}

class _Notif {
  final IconData icon;
  final Color color;
  final String title, body, time;
  final bool read;
  const _Notif({required this.icon, required this.color, required this.title,
      required this.body, required this.time, required this.read});
}

class _NotifCard extends StatelessWidget {
  final _Notif notif;
  final dynamic colors;
  const _NotifCard({required this.notif, required this.colors});

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: notif.read ? colors.surface : notif.color.withValues(alpha: 0.05),
      borderRadius: BorderRadius.circular(rMD),
      border: Border.all(
        color: notif.read ? Colors.transparent : notif.color.withValues(alpha: 0.2),
      ),
      boxShadow: [colors.cardShadowStyle],
    ),
    child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Container(
        width: 38, height: 38,
        decoration: BoxDecoration(
          color: notif.color.withValues(alpha: 0.12),
          shape: BoxShape.circle,
        ),
        child: Icon(notif.icon, size: 18, color: notif.color),
      ),
      const SizedBox(width: 12),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Expanded(child: Text(notif.title, style: GoogleFonts.inter(
            fontSize: 13, fontWeight: FontWeight.w700, color: colors.textPrimary,
          ))),
          if (!notif.read)
            Container(width: 8, height: 8,
                decoration: const BoxDecoration(color: kAccent, shape: BoxShape.circle)),
        ]),
        const SizedBox(height: 3),
        Text(notif.body, style: GoogleFonts.inter(fontSize: 12, color: colors.textSecondary)),
        const SizedBox(height: 5),
        Text(notif.time, style: GoogleFonts.inter(fontSize: 10, color: colors.textHint)),
      ])),
    ]),
  );
}
