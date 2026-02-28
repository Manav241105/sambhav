import 'package:flutter/material.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/typography.dart';

class NotificationsScreen extends StatelessWidget {
  const NotificationsScreen({super.key});

  static const _items = [
    _NotifData(icon: Icons.warning_amber_rounded, color: kDanger,
      title: 'P0 — Brake Pads Critical', body: '2.1mm — below safe threshold', time: '5 min ago'),
    _NotifData(icon: Icons.calendar_today_outlined, color: kAccentDark,
      title: 'Booking Confirmed', body: 'Mar 2 · 10:00 AM · Bay 3', time: '1 hr ago'),
    _NotifData(icon: Icons.battery_3_bar, color: kWarning,
      title: 'Battery Warning', body: '11.8V — monitor closely', time: '2 hrs ago'),
    _NotifData(icon: Icons.check_circle_outline, color: kGood,
      title: 'Service Completed', body: 'Oil Change on Feb 15', time: 'Yesterday'),
  ];

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: kBg,
    appBar: AppBar(backgroundColor: kBg, elevation: 0, title: Text('Notifications', style: kTitle())),
    body: ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: _items.length,
      separatorBuilder: (_, __) => const SizedBox(height: 10),
      itemBuilder: (_, i) {
        final n = _items[i];
        return Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(color: kSurface, borderRadius: BorderRadius.circular(rLG),
            boxShadow: const [cardShadow]),
          child: Row(children: [
            Container(width: 42, height: 42,
              decoration: BoxDecoration(color: n.color.withOpacity(0.12), shape: BoxShape.circle),
              child: Icon(n.icon, size: 20, color: n.color)),
            const SizedBox(width: 12),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(n.title, style: kLabel(color: kDark)),
              Text(n.body, style: kCaption()),
            ])),
            Text(n.time, style: kCaption()),
          ]),
        );
      },
    ),
  );
}

class _NotifData {
  final IconData icon;
  final Color color;
  final String title, body, time;
  const _NotifData({required this.icon, required this.color, required this.title,
    required this.body, required this.time});
}
