import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/typography.dart';
import '../../core/providers/booking_provider.dart';
import 'package:go_router/go_router.dart';

class BookingFlowScreen extends ConsumerStatefulWidget {
  const BookingFlowScreen({super.key});
  @override
  ConsumerState<BookingFlowScreen> createState() => _BookingFlowScreenState();
}

class _BookingFlowScreenState extends ConsumerState<BookingFlowScreen> {
  int _step = 0;
  String? _service;
  DateTime? _date;
  String? _slot;
  bool _loading = false;

  static const _services = ['Brake Pads', 'Battery', 'Oil Change', 'Full Service', 'Diagnostics'];
  static const _slots = ['9:00 AM', '10:00 AM', '11:00 AM', '2:00 PM', '3:30 PM'];

  Future<void> _onNext() async {
    if (_step == 0) {
      if (_service == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please select a service first')),
        );
        return;
      }
      setState(() => _step++);
    } else if (_step == 1) {
      if (_date == null || _slot == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please pick a date and time slot first')),
        );
        return;
      }
      setState(() => _step++);
    } else {
      // Step 2 — confirm & call API
      setState(() => _loading = true);
      try {
        int hour = int.parse(_slot!.split(':')[0]);
        if (_slot!.contains('PM') && hour != 12) hour += 12;
        if (_slot!.contains('AM') && hour == 12) hour = 0;
        int min = int.parse(_slot!.split(':')[1].split(' ')[0]);
        final exactTime = DateTime(_date!.year, _date!.month, _date!.day, hour, min);

        final bookingData = await ref.read(bookingProvider.notifier).createBooking({
          'service_component': _service!.toLowerCase().replaceAll(' ', '_'),
          'slot_time': '${_date!.day}/${_date!.month} at $_slot',
          'slot_time_iso': exactTime.toIso8601String(),
          'technician_name': 'Rajesh Kumar',
          'bay': 'BAY-3',
        });

        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(children: [
              const Icon(Icons.check_circle, color: Colors.white, size: 20),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  'Booking confirmed! $_service at $_slot',
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
              ),
            ]),
            backgroundColor: kGood,
            duration: const Duration(seconds: 4),
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        );
        if (context.mounted) context.pop(bookingData);
      } catch (e) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Booking failed: $e'),
            backgroundColor: kDanger,
            behavior: SnackBarBehavior.floating,
          ),
        );
      } finally {
        if (mounted) setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.appColors;

    return Scaffold(
      backgroundColor: colors.scaffoldBg,
      appBar: AppBar(
        backgroundColor: colors.scaffoldBg, elevation: 0,
        title: Text('Book Service — Step ${_step + 1}/3', style: kSubtitle(color: colors.textPrimary)),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(children: [
          // Step indicator
          Row(children: List.generate(3, (i) => Expanded(child: Container(
            height: 4, margin: const EdgeInsets.symmetric(horizontal: 3),
            decoration: BoxDecoration(
              color: i <= _step ? kAccent : colors.neuBg,
              borderRadius: BorderRadius.circular(rFull),
            ),
          )))),
          const SizedBox(height: 24),

          if (_step == 0) ...[
            Text('Select Service', style: kTitle(color: colors.textPrimary)),
            const SizedBox(height: 16),
            ..._services.map((s) => GestureDetector(
              onTap: () => setState(() { _service = s; }),
              child: Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: _service == s ? kAccent.withValues(alpha: 0.15) : colors.surface,
                  borderRadius: BorderRadius.circular(rMD),
                  border: Border.all(color: _service == s ? kAccent : Colors.transparent),
                  boxShadow: [colors.cardShadowStyle],
                ),
                child: Text(s, style: kBody(color: colors.textPrimary)),
              ),
            )),
          ],

          if (_step == 1) ...[
            Text('Pick a Date & Time', style: kTitle(color: colors.textPrimary)),
            const SizedBox(height: 16),
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
                        borderRadius: BorderRadius.circular(rMD),
                        border: Border.all(color: isSelected ? kAccent : colors.navBorder),
                      ),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][d.weekday - 1],
                            style: kLabel(color: isSelected ? kDark : colors.textSecondary)
                          ),
                          Text('${d.day}/${d.month}', style: kBody(color: isSelected ? kDark : colors.textPrimary)),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 16),
            Wrap(spacing: 10, runSpacing: 10,
              children: _slots.map((sl) => GestureDetector(
                onTap: () => setState(() => _slot = sl),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                  decoration: BoxDecoration(
                    color: _slot == sl ? kAccent : colors.surface,
                    borderRadius: BorderRadius.circular(rMD),
                    boxShadow: [colors.cardShadowStyle],
                  ),
                  child: Text(sl, style: kLabel(color: _slot == sl ? kDark : colors.textSecondary)),
                ),
              )).toList(),
            ),
          ],

          if (_step == 2) ...[
            Text('Confirm Booking', style: kTitle(color: colors.textPrimary)),
            const SizedBox(height: 16),
            Container(padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: colors.surface,
                borderRadius: BorderRadius.circular(rLG),
                boxShadow: [colors.cardShadowStyle],
              ),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                _InfoLine('Service', _service ?? '-'),
                _InfoLine('Date', _date != null ? '${_date!.day}/${_date!.month}/${_date!.year}' : '-'),
                _InfoLine('Time', _slot ?? '-'),
                _InfoLine('Bay', 'Bay 3 (auto-assigned)'),
                _InfoLine('Technician', 'Rajesh Kumar'),
              ]),
            ),
          ],

          const Spacer(),
          GestureDetector(
            onTap: _loading ? null : _onNext,
            child: Container(
              height: 52, width: double.infinity,
              decoration: BoxDecoration(
                color: _loading ? kAccent.withValues(alpha: 0.6) : kAccent,
                borderRadius: BorderRadius.circular(rMD),
              ),
              child: Center(
                child: _loading
                    ? const SizedBox(
                        width: 22, height: 22,
                        child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.5),
                      )
                    : Text(
                        _step == 2 ? 'Confirm Booking' : 'Next',
                        style: kSubtitle(color: kDark),
                      ),
              ),
            ),
          ),
        ]),
      ),
    );
  }
}

class _InfoLine extends StatelessWidget {
  final String label, value;
  const _InfoLine(this.label, this.value);
  @override
  Widget build(BuildContext context) {
    final colors = context.appColors;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Text(label, style: kBody(color: colors.textSecondary)),
        Text(value, style: kLabel(color: colors.textPrimary)),
      ]),
    );
  }
}
