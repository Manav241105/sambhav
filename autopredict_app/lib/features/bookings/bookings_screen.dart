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

        // Actions
        if ((booking['status'] as String? ?? '').toUpperCase() != 'CANCELLED') ...[
          const SizedBox(height: 12),
          Row(children: [
            GestureDetector(
              onTap: onCancel,
              child: Text('Cancel', style: GoogleFonts.inter(
                  fontSize: 12, color: kDanger, fontWeight: FontWeight.w600)),
            ),
            const SizedBox(width: 24),
            GestureDetector(
              onTap: () {
                showModalBottomSheet(
                  context: context,
                  isScrollControlled: true,
                  backgroundColor: Colors.transparent,
                  builder: (ctx) => _RescheduleSheet(booking: booking, colors: colors),
                );
              },
              child: Text('Reschedule', style: GoogleFonts.inter(
                  fontSize: 12, color: kAccentDark, fontWeight: FontWeight.w600)),
            ),
          ]),
        ],
      ]),
    );
  }
}

class _RescheduleSheet extends ConsumerStatefulWidget {
  final Map<String, dynamic> booking;
  final dynamic colors;
  const _RescheduleSheet({required this.booking, required this.colors});

  @override
  ConsumerState<_RescheduleSheet> createState() => _RescheduleSheetState();
}

class _RescheduleSheetState extends ConsumerState<_RescheduleSheet> {
  DateTime? _date;
  String? _slot;
  bool _loading = false;
  static const _slots = ['9:00 AM', '10:00 AM', '11:00 AM', '2:00 PM', '3:30 PM'];

  Future<void> _save() async {
    if (_date == null || _slot == null) return;
    setState(() => _loading = true);
    try {
      int hour = int.parse(_slot!.split(':')[0]);
      if (_slot!.contains('PM') && hour != 12) hour += 12;
      if (_slot!.contains('AM') && hour == 12) hour = 0;
      int min = int.parse(_slot!.split(':')[1].split(' ')[0]);
      final exactTime = DateTime(_date!.year, _date!.month, _date!.day, hour, min);

      await ref.read(bookingProvider.notifier).rescheduleBooking(
        widget.booking['booking_id'],
        {
          'slot_time': '${_date!.day}/${_date!.month} at $_slot',
          'slot_time_iso': exactTime.toIso8601String(),
        }
      );
      if (mounted) Navigator.pop(context);
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = widget.colors;
    return Container(
      padding: EdgeInsets.fromLTRB(20, 20, 20, MediaQuery.of(context).viewInsets.bottom + 20),
      decoration: BoxDecoration(
        color: colors.scaffoldBg,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Reschedule Booking', style: kTitle(color: colors.textPrimary)),
          const SizedBox(height: 16),
          // Date Picker
          SizedBox(
            height: 70,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: 14,
              itemBuilder: (context, i) {
                final d = DateTime.now().add(Duration(days: i + 1));
                final isSelected = _date?.day == d.day && _date?.month == d.month;
                return GestureDetector(
                  onTap: () => setState(() => _date = d),
                  child: Container(
                    width: 65,
                    margin: const EdgeInsets.only(right: 10),
                    decoration: BoxDecoration(
                      color: isSelected ? kAccent : colors.surface,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: isSelected ? kAccent : colors.navBorder),
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][d.weekday - 1], style: kLabel(color: isSelected ? Colors.black : colors.textSecondary)),
                        Text('${d.day}/${d.month}', style: kBody(color: isSelected ? Colors.black : colors.textPrimary)),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: 16),
          // Time Picker
          Wrap(spacing: 10, runSpacing: 10,
            children: _slots.map((sl) => GestureDetector(
              onTap: () => setState(() => _slot = sl),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                decoration: BoxDecoration(
                  color: _slot == sl ? kAccent : colors.surface,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(sl, style: kLabel(color: _slot == sl ? Colors.black : colors.textSecondary)),
              ),
            )).toList(),
          ),
          const SizedBox(height: 24),
          // Save Button
          GestureDetector(
            onTap: _loading ? null : _save,
            child: Container(
              height: 52, width: double.infinity,
              decoration: BoxDecoration(
                color: _loading || _date == null || _slot == null ? kAccent.withValues(alpha: 0.5) : kAccent,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Center(
                child: _loading
                    ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : Text('Confirm Reschedule', style: kSubtitle(color: Colors.black)),
              ),
            ),
          ),
        ],
      ),
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
