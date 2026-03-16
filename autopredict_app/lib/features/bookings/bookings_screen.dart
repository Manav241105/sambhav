import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/typography.dart';

class BookingsScreen extends StatelessWidget {
  const BookingsScreen({super.key});

  static const _bookings = [
    _BookingData(date: 'Mar 2, 2026', time: '10:00 AM', bay: 'Bay 3', tech: 'Rajesh Kumar',
        service: 'Brake Pads', status: 'CONFIRMED'),
    _BookingData(date: 'Mar 8, 2026', time: '2:00 PM', bay: 'Bay 1', tech: 'Amit Sharma',
        service: 'Battery Check', status: 'CONFIRMED'),
    _BookingData(date: 'Feb 15, 2026', time: '11:00 AM', bay: 'Bay 2', tech: 'Priya Nair',
        service: 'Oil Change', status: 'COMPLETED'),
  ];

  @override
  Widget build(BuildContext context) {
    final colors = context.appColors;

    return Scaffold(
      backgroundColor: colors.scaffoldBg,
      appBar: AppBar(
        backgroundColor: colors.scaffoldBg, elevation: 0,
        title: Text('My Bookings', style: kTitle(color: colors.textPrimary)),
        actions: [
          TextButton(
            onPressed: () {},
            child: Text('+ New', style: kLabel(color: kAccentDark)),
          ),
        ],
      ),
      body: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: _bookings.length,
        separatorBuilder: (_, __) => const SizedBox(height: 12),
        itemBuilder: (_, i) => _BookingCard(data: _bookings[i]),
      ),
    );
  }
}

class _BookingData {
  final String date, time, bay, tech, service, status;
  const _BookingData({required this.date, required this.time, required this.bay,
    required this.tech, required this.service, required this.status});
}

class _BookingCard extends StatelessWidget {
  final _BookingData data;
  const _BookingCard({super.key, required this.data});

  Color get _statusColor => switch (data.status) {
    'IN_PROGRESS' => kFuelOrange,
    'COMPLETED'   => kGood,
    _ => kAccentDark,
  };

  @override
  Widget build(BuildContext context) {
    final colors = context.appColors;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(rLG),
        boxShadow: [colors.cardShadowStyle],
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Text(data.service, style: kSubtitle(color: colors.textPrimary)),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: _statusColor.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(rFull),
            ),
            child: Text(data.status, style: kCaption(color: _statusColor)),
          ),
        ]),
        const SizedBox(height: 10),
        _Row(icon: Icons.calendar_today_outlined, text: '${data.date} · ${data.time}'),
        _Row(icon: Icons.location_on_outlined, text: '${data.bay} · ${data.tech}'),
      ]),
    );
  }
}

class _Row extends StatelessWidget {
  final IconData icon; final String text;
  const _Row({required this.icon, required this.text});
  @override
  Widget build(BuildContext context) {
    final colors = context.appColors;

    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(children: [
        Icon(icon, size: 14, color: colors.textSecondary), const SizedBox(width: 8),
        Text(text, style: kBody(color: colors.textSecondary)),
      ]),
    );
  }
}
