import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/typography.dart';
import '../../core/providers/booking_provider.dart';

class BookingsScreen extends ConsumerWidget {
  const BookingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.appColors;
    final bookingsAsync = ref.watch(bookingProvider);

    return Scaffold(
      backgroundColor: colors.scaffoldBg,
      appBar: AppBar(
        backgroundColor: colors.scaffoldBg, elevation: 0,
        title: Text('Bookings', style: kTitle(color: colors.textPrimary)),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: colors.textSecondary),
            onPressed: () => ref.read(bookingProvider.notifier).refresh(),
          ),
        ],
      ),
      body: bookingsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator(color: kAccent)),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (bookings) => bookings.isEmpty
            ? _EmptyState(colors: colors)
            : _BookingList(bookings: bookings, colors: colors, ref: ref),
      ),
    );
  }
}

class _BookingList extends StatelessWidget {
  final List<Map<String, dynamic>> bookings;
  final dynamic colors;
  final WidgetRef ref;
  const _BookingList({required this.bookings, required this.colors, required this.ref});

  @override
  Widget build(BuildContext context) => ListView.separated(
    padding: const EdgeInsets.all(16),
    itemCount: bookings.length,
    separatorBuilder: (_, __) => const SizedBox(height: 12),
    itemBuilder: (_, i) => _BookingCard(booking: bookings[i], colors: colors,
        onCancel: () => ref.read(bookingProvider.notifier)
            .cancelBooking(bookings[i]['booking_id'])),
  );
}

class _BookingCard extends StatelessWidget {
  final Map<String, dynamic> booking;
  final dynamic colors;
  final VoidCallback onCancel;
  const _BookingCard({required this.booking, required this.colors, required this.onCancel});

  Color get _statusColor => switch ((booking['status'] as String? ?? '').toUpperCase()) {
    'CONFIRMED' => kGood,
    'PENDING'   => kWarning,
    'CANCELLED' => kDanger,
    _ => kMid,
  };

  @override
  Widget build(BuildContext context) {
    final component = (booking['service_component'] as String? ?? 'Service')
        .replaceAll('_', ' ')
        .split(' ')
        .map((w) => w.isEmpty ? '' : w[0].toUpperCase() + w.substring(1))
        .join(' ');

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(rLG),
        boxShadow: [colors.cardShadowStyle],
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        // Header
        Row(children: [
          Container(
            width: 40, height: 40,
            decoration: BoxDecoration(
              color: kAccent.withValues(alpha: 0.12),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.build_outlined, size: 18, color: kAccentDark),
          ),
          const SizedBox(width: 12),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(component, style: GoogleFonts.inter(
              fontSize: 15, fontWeight: FontWeight.w700, color: colors.textPrimary,
            )),
            Text(booking['booking_id'] ?? '', style: GoogleFonts.inter(
              fontSize: 11, color: colors.textSecondary,
            )),
          ])),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: _statusColor.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(rFull),
            ),
            child: Text((booking['status'] ?? 'PENDING').toString().toUpperCase(),
                style: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w700,
                    color: _statusColor)),
          ),
        ]),
        const SizedBox(height: 14),

        // Details
        Wrap(spacing: 16, runSpacing: 8, children: [
          _Detail(icon: Icons.calendar_today_outlined,
              text: booking['slot_time'] ?? 'TBD', colors: colors),
          _Detail(icon: Icons.person_outline,
              text: booking['technician_name'] ?? 'TBD', colors: colors),
          _Detail(icon: Icons.garage_outlined,
              text: booking['bay'] ?? 'TBD', colors: colors),
          if (booking['service_duration_hours'] != null)
            _Detail(icon: Icons.timer_outlined,
                text: '${booking['service_duration_hours']}h', colors: colors),
        ]),

        // Status stepper
        const SizedBox(height: 16),
        _StatusStepper(status: booking['status'] ?? 'CONFIRMED', colors: colors),

        // Cancel
        if ((booking['status'] as String? ?? '').toUpperCase() != 'CANCELLED') ...[
          const SizedBox(height: 12),
          GestureDetector(
            onTap: onCancel,
            child: Text('Cancel Booking', style: GoogleFonts.inter(
                fontSize: 12, color: kDanger, fontWeight: FontWeight.w600)),
          ),
        ],
      ]),
    );
  }
}

class _StatusStepper extends StatelessWidget {
  final String status;
  final dynamic colors;
  const _StatusStepper({required this.status, required this.colors});

  @override
  Widget build(BuildContext context) {
    final steps = ['CONFIRMED', 'IN SERVICE', 'COMPLETED'];
    final currentIdx = switch (status.toUpperCase()) {
      'CONFIRMED' => 0,
      'IN_SERVICE' || 'IN SERVICE' => 1,
      'COMPLETED' => 2,
      _ => 0,
    };

    return Row(children: steps.asMap().entries.map((e) {
      final active = e.key <= currentIdx;
      return Expanded(child: Row(children: [
        Expanded(child: Column(children: [
          Container(
            width: 24, height: 24,
            decoration: BoxDecoration(
              color: active ? kAccent : colors.neuBg,
              shape: BoxShape.circle,
            ),
            child: Icon(active ? Icons.check : Icons.circle_outlined,
                size: 12, color: active ? kDark : colors.textSecondary),
          ),
          const SizedBox(height: 4),
          Text(e.value, style: GoogleFonts.inter(
            fontSize: 9, color: active ? kAccentDark : colors.textSecondary,
            fontWeight: active ? FontWeight.w600 : FontWeight.w400,
          ), textAlign: TextAlign.center),
        ])),
        if (e.key < steps.length - 1)
          Expanded(child: Container(
            height: 2,
            color: e.key < currentIdx ? kAccent : colors.gaugeTrackColor,
          )),
      ]));
    }).toList());
  }
}

class _Detail extends StatelessWidget {
  final IconData icon;
  final String text;
  final dynamic colors;
  const _Detail({required this.icon, required this.text, required this.colors});

  @override
  Widget build(BuildContext context) => Row(mainAxisSize: MainAxisSize.min, children: [
    Icon(icon, size: 13, color: colors.textSecondary),
    const SizedBox(width: 4),
    Text(text, style: GoogleFonts.inter(fontSize: 12, color: colors.textSecondary)),
  ]);
}

class _EmptyState extends StatelessWidget {
  final dynamic colors;
  const _EmptyState({required this.colors});

  @override
  Widget build(BuildContext context) => Center(
    child: Column(mainAxisSize: MainAxisSize.min, children: [
      Icon(Icons.calendar_today_outlined, size: 48, color: colors.textSecondary),
      const SizedBox(height: 16),
      Text('No bookings yet', style: GoogleFonts.inter(
        fontSize: 16, fontWeight: FontWeight.w600, color: colors.textSecondary,
      )),
      const SizedBox(height: 8),
      Text('Ask the AI to book a service', style: GoogleFonts.inter(
        fontSize: 13, color: colors.textHint,
      )),
    ]),
  );
}
