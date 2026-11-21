import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/typography.dart';
import '../../core/providers/booking_provider.dart';
import '../../core/services/api_service.dart';

class BookingFlowScreen extends ConsumerStatefulWidget {
  const BookingFlowScreen({super.key});
  @override
  ConsumerState<BookingFlowScreen> createState() => _BookingFlowScreenState();
}

class _BookingFlowScreenState extends ConsumerState<BookingFlowScreen> {
  int _step = 0;
  String? _service;
  Map<String, dynamic>? _slot; // {slot_time, slot_time_iso}
  bool _loading = false;

  // Jobs the workshop offers (must match the API's service components).
  static const _services = ['Brake Pads', 'Battery', 'Oil Change', 'Tires', 'Cooling System', 'Full Service'];

  final _api = ApiService();
  late final List<DateTime> _days = List.generate(7, (i) => DateTime.now().add(Duration(days: i + 1)));
  int _dayIndex = 0;
  Future<List<Map<String, dynamic>>>? _slotsFuture;

  String _isoDate(DateTime d) =>
      '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  void _loadSlots() {
    _slot = null;
    _slotsFuture = _api.getAvailableSlots(_isoDate(_days[_dayIndex]), component: _service!);
  }

  static const _weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  Future<void> _onNext() async {
    if (_step == 0) {
      if (_service == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please select a service first')),
        );
        return;
      }
      setState(() {
        _step++;
        _loadSlots();
      });
    } else if (_step == 1) {
      if (_slot == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please pick a time slot first')),
        );
        return;
      }
      setState(() => _step++);
    } else {
      // Step 2 — confirm & call API
      setState(() => _loading = true);
      try {
        final booking = await ref.read(bookingProvider.notifier).createBooking(
          component: _service!,
          slotTimeIso: _slot!['slot_time_iso'] as String,
        );

        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(children: [
              const Icon(Icons.check_circle, color: Colors.white, size: 20),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  'Booked: $_service, ${booking['slot_time'] ?? _slot!['slot_time']} with ${booking['technician_name'] ?? 'the workshop'}',
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
        Navigator.pop(context);
      } catch (e) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(e.toString()),
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
            Text('Pick a Time Slot', style: kTitle(color: colors.textPrimary)),
            const SizedBox(height: 12),
            SizedBox(
              height: 44,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: _days.length,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (_, i) {
                  final d = _days[i];
                  final selected = i == _dayIndex;
                  return GestureDetector(
                    onTap: () => setState(() { _dayIndex = i; _loadSlots(); }),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      decoration: BoxDecoration(
                        color: selected ? kAccent : colors.surface,
                        borderRadius: BorderRadius.circular(rMD),
                      ),
                      child: Text('${_weekdays[d.weekday - 1]} ${d.day}',
                          style: kLabel(color: selected ? kDark : colors.textSecondary)),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 16),
            FutureBuilder<List<Map<String, dynamic>>>(
              future: _slotsFuture,
              builder: (context, snap) {
                if (snap.connectionState != ConnectionState.done) {
                  return const Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator());
                }
                if (snap.hasError) {
                  return Text(snap.error.toString(), style: kBody(color: kDanger));
                }
                final slots = snap.data ?? [];
                if (slots.isEmpty) {
                  return Text('No free slots this day. Try another day.', style: kBody(color: colors.textSecondary));
                }
                return Wrap(spacing: 10, runSpacing: 10,
                  children: slots.map((sl) {
                    final selected = _slot?['slot_time_iso'] == sl['slot_time_iso'];
                    return GestureDetector(
                      onTap: () => setState(() => _slot = sl),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                        decoration: BoxDecoration(
                          color: selected ? kAccent : colors.surface,
                          borderRadius: BorderRadius.circular(rMD),
                          boxShadow: [colors.cardShadowStyle],
                        ),
                        child: Text(sl['slot_time'] as String,
                            style: kLabel(color: selected ? kDark : colors.textSecondary)),
                      ),
                    );
                  }).toList(),
                );
              },
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
                _InfoLine('Day', '${_weekdays[_days[_dayIndex].weekday - 1]} ${_days[_dayIndex].day}'),
                _InfoLine('Time', (_slot?['slot_time'] as String?) ?? '-'),
                _InfoLine('Technician & bay', 'Assigned by the workshop'),
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
