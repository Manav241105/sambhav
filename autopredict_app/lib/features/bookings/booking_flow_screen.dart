import 'package:flutter/material.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/typography.dart';

// Stub for booking flow — 3 steps
class BookingFlowScreen extends StatefulWidget {
  const BookingFlowScreen({super.key});
  @override
  State<BookingFlowScreen> createState() => _BookingFlowScreenState();
}

class _BookingFlowScreenState extends State<BookingFlowScreen> {
  int _step = 0;
  String? _service;
  String? _slot;

  static const _services = ['Brake Pads', 'Battery', 'Oil Change', 'Full Service', 'Diagnostics'];
  static const _slots = ['9:00 AM', '10:00 AM', '11:00 AM', '2:00 PM', '3:30 PM'];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      appBar: AppBar(
        backgroundColor: kBg, elevation: 0,
        title: Text('Book Service — Step ${_step + 1}/3', style: kSubtitle()),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(children: [
          // Step indicator
          Row(children: List.generate(3, (i) => Expanded(child: Container(
            height: 4, margin: const EdgeInsets.symmetric(horizontal: 3),
            decoration: BoxDecoration(
              color: i <= _step ? kAccent : kSubtle,
              borderRadius: BorderRadius.circular(rFull),
            ),
          )))),
          const SizedBox(height: 24),

          if (_step == 0) ...[
            Text('Select Service', style: kTitle()),
            const SizedBox(height: 16),
            ..._services.map((s) => GestureDetector(
              onTap: () => setState(() { _service = s; }),
              child: Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: _service == s ? kAccent.withOpacity(0.15) : kSurface,
                  borderRadius: BorderRadius.circular(rMD),
                  border: Border.all(color: _service == s ? kAccent : Colors.transparent),
                  boxShadow: const [cardShadow],
                ),
                child: Text(s, style: kBody(color: kDark)),
              ),
            )),
          ],

          if (_step == 1) ...[
            Text('Pick a Time Slot', style: kTitle()),
            const SizedBox(height: 16),
            Wrap(spacing: 10, runSpacing: 10,
              children: _slots.map((sl) => GestureDetector(
                onTap: () => setState(() => _slot = sl),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                  decoration: BoxDecoration(
                    color: _slot == sl ? kAccent : kSurface,
                    borderRadius: BorderRadius.circular(rMD),
                    boxShadow: const [cardShadow],
                  ),
                  child: Text(sl, style: kLabel(color: _slot == sl ? kDark : kMid)),
                ),
              )).toList(),
            ),
          ],

          if (_step == 2) ...[
            Text('Confirm Booking', style: kTitle()),
            const SizedBox(height: 16),
            Container(padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(color: kSurface, borderRadius: BorderRadius.circular(rLG),
                boxShadow: const [cardShadow]),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                _InfoLine('Service', _service ?? '-'),
                _InfoLine('Time', _slot ?? '-'),
                _InfoLine('Bay', 'Bay 3 (auto-assigned)'),
                _InfoLine('Technician', 'Rajesh Kumar'),
              ]),
            ),
          ],

          const Spacer(),
          GestureDetector(
            onTap: () {
              if (_step < 2) setState(() => _step++);
              else Navigator.pop(context);
            },
            child: Container(
              height: 52, width: double.infinity,
              decoration: BoxDecoration(color: kAccent, borderRadius: BorderRadius.circular(rMD)),
              child: Center(child: Text(_step == 2 ? 'Confirm' : 'Next', style: kSubtitle(color: kDark))),
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
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 12),
    child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
      Text(label, style: kBody()),
      Text(value, style: kLabel(color: kDark)),
    ]),
  );
}
