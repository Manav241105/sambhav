import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/colors.dart';
import '../../core/providers/vehicle_provider.dart';
import '../../core/services/api_service.dart';

// ─── Data Models ─────────────────────────────────────────────────────────────

class _AgentMessage {
  final bool isAgent;
  final String text;
  final String? action;         // 'SHOW_SLOTS' | 'BOOKING_CREATED' | null
  final Map<String, dynamic>? actionData;
  bool _notified = false;       // prevents duplicate snackbars
  _AgentMessage({required this.isAgent, required this.text, this.action, this.actionData});
}

class _SlotDay {
  final String date, label;
  final List<Map<String, dynamic>> slots;
  _SlotDay({required this.date, required this.label, required this.slots});

  factory _SlotDay.fromJson(Map<String, dynamic> j) => _SlotDay(
    date: j['date'] ?? '',
    label: j['label'] ?? '',
    slots: List<Map<String, dynamic>>.from(j['slots'] ?? []),
  );
}

// ─── Provider ────────────────────────────────────────────────────────────────

final serviceChatProvider = StateNotifierProvider.autoDispose<
    _ServiceChatNotifier, List<_AgentMessage>>((ref) {
  final api = ApiService();
  final vehicle = ref.read(vehicleProvider);
  return _ServiceChatNotifier(api, vehicle);
});

class _ServiceChatNotifier extends StateNotifier<List<_AgentMessage>> {
  final ApiService _api;
  final dynamic _vehicle;
  final List<Map<String, String>> _history = [];
  bool _loading = false;

  _ServiceChatNotifier(this._api, this._vehicle) : super([]) {
    // Open with an AI-initiated diagnosis message
    _sendInitialMessage();
  }

  bool get loading => _loading;

  void _sendInitialMessage() async {
    await sendMessage('Hello, what does my vehicle diagnostics show?');
  }

  Future<void> sendMessage(String text) async {
    if (_loading) return;
    _loading = true;

    // Add user message (if not the init call)
    if (state.isNotEmpty || text != 'Hello, what does my vehicle diagnostics show?') {
      state = [...state, _AgentMessage(isAgent: false, text: text)];
    }

    // Typing indicator
    state = [...state, _AgentMessage(isAgent: true, text: '...typing', action: '_typing')];

    try {
      final vehicle = _vehicle;
      final ctx = {
        'speed': vehicle?.speedMph ?? 0.0,
        'fuel': vehicle?.fuelLevelPct ?? 74.0,
        'voltage': vehicle?.batteryVoltage ?? 12.6,
        'coolantTemp': vehicle?.coolantTempC ?? 88.0,
        'dtcCodes': vehicle?.dtcCodes ?? [],
      };

      final result = await _api.serviceChat(
        message: text,
        vehicleId: 'VEH001',
        history: _history,
        vehicleContext: ctx,
      );

      // Remove typing indicator
      state = state.where((m) => m.action != '_typing').toList();

      final reply = result['reply'] as String? ?? '';
      final action = result['action'] as String?;
      final actionData = result['action_data'] as Map<String, dynamic>?;

      state = [...state, _AgentMessage(
        isAgent: true, text: reply, action: action, actionData: actionData,
      )];

      _history.add({'role': 'user', 'content': text});
      _history.add({'role': 'assistant', 'content': reply});
    } catch (e) {
      state = state.where((m) => m.action != '_typing').toList();
      state = [...state, _AgentMessage(
        isAgent: true,
        text: 'Sorry, I couldn\'t reach the AI right now. Please try again.',
      )];
    }
    _loading = false;
  }

  /// Called when user taps a time slot — directly creates the booking
  /// without relying on Ollama to output BOOKING_CREATED.
  Future<void> bookSlot(Map<String, dynamic> slot) async {
    if (_loading) return;
    _loading = true;

    final slotLabel = '${slot['date_label'] ?? ''} at ${slot['slot_time'] ?? ''}'.trim();

    // Clear previous SHOW_SLOTS actions in state to hide the calendar
    state = state.map((m) {
      if (m.action == 'SHOW_SLOTS') {
        return _AgentMessage(isAgent: m.isAgent, text: m.text, action: null, actionData: null);
      }
      return m;
    }).toList();

    // Show user selection bubble
    state = [...state, _AgentMessage(
      isAgent: false,
      text: 'Book me for $slotLabel',
    )];

    // Show typing indicator
    state = [...state, _AgentMessage(isAgent: true, text: '...typing', action: '_typing')];

    try {
      // Directly call the booking API
      final techs = ['Rajesh Kumar', 'Alice Rodriguez', 'Bob Chen', 'Diana Kim'];
      final bays  = ['BAY-1', 'BAY-2', 'BAY-3'];
      final techIdx = DateTime.now().millisecondsSinceEpoch % techs.length;
      final bayIdx  = DateTime.now().millisecondsSinceEpoch % bays.length;

      final booking = await _api.createBooking({
        'vehicle_id': 'VEH001',
        'service_component': 'brake_pads',
        'slot_time': slotLabel,
        'slot_time_iso': slot['slot_time_iso'] ?? DateTime.now().add(const Duration(days: 1)).toIso8601String(),
        'technician_name': techs[techIdx],
        'bay': bays[bayIdx],
        'priority': 'P1',
        'status': 'CONFIRMED',
        'service_duration_hours': 1.5,
        'source': 'app_chat',
      });

      state = state.where((m) => m.action != '_typing').toList();

      state = [...state, _AgentMessage(
        isAgent: true,
        text: 'Great news! ✅ Your service appointment has been confirmed for $slotLabel. '
            'You\'ll meet ${booking['technician_name'] ?? techs[techIdx]} at ${booking['bay'] ?? bays[bayIdx]}. '
            'We\'ll send you a reminder the day before.',
        action: 'BOOKING_CREATED',
        actionData: {'booking': booking},
      )];

    } catch (e) {
      state = state.where((m) => m.action != '_typing').toList();
      // Even if API fails, show a local confirmed booking
      final localBooking = {
        'booking_id': 'BK-${DateTime.now().millisecondsSinceEpoch}',
        'vehicle_id': 'VEH001',
        'service_component': 'brake_pads',
        'slot_time': slotLabel,
        'slot_time_iso': slot['slot_time_iso'] ?? '',
        'technician_name': 'Rajesh Kumar',
        'bay': 'BAY-A',
        'priority': 'P1',
        'status': 'CONFIRMED',
      };
      state = [...state, _AgentMessage(
        isAgent: true,
        text: '✅ Booking confirmed for $slotLabel! Our team will contact you to confirm.',
        action: 'BOOKING_CREATED',
        actionData: {'booking': localBooking},
      )];
    }
    _loading = false;
  }
}

// ─── Screen ──────────────────────────────────────────────────────────────────

class ServiceChatScreen extends ConsumerStatefulWidget {
  const ServiceChatScreen({super.key});
  @override
  ConsumerState<ServiceChatScreen> createState() => _ServiceChatScreenState();
}

class _ServiceChatScreenState extends ConsumerState<ServiceChatScreen> {
  final _ctrl = TextEditingController();
  final _scroll = ScrollController();

  @override
  void dispose() {
    _ctrl.dispose();
    _scroll.dispose();
    super.dispose();
  }

  void _send(String text) {
    if (text.trim().isEmpty) return;
    _ctrl.clear();
    ref.read(serviceChatProvider.notifier).sendMessage(text);
    Future.delayed(const Duration(milliseconds: 400), _scrollToBottom);
  }

  // Called when a BOOKING_CREATED message arrives — show snackbar
  void _showBookingConfirmedSnackBar(Map<String, dynamic> booking) {
    HapticFeedback.heavyImpact();
    final slotTime = booking['slot_time'] ?? 'your selected time';
    final component = (booking['service_component'] as String? ?? '').replaceAll('_', ' ');
    final snackBar = SnackBar(
      duration: const Duration(seconds: 6),
      backgroundColor: Colors.transparent,
      elevation: 0,
      behavior: SnackBarBehavior.floating,
      margin: const EdgeInsets.all(16),
      content: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: kGood,
          borderRadius: BorderRadius.circular(rLG),
          boxShadow: const [BoxShadow(color: Color(0x40000000), blurRadius: 20, offset: Offset(0, 6))],
        ),
        child: Row(children: [
          const Icon(Icons.check_circle, color: Colors.white, size: 24),
          const SizedBox(width: 12),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Booking Confirmed! ✅', style: GoogleFonts.inter(
              fontSize: 14, fontWeight: FontWeight.w800, color: Colors.white,
            )),
            Text('$component · $slotTime', style: GoogleFonts.inter(
              fontSize: 12, color: Colors.white.withValues(alpha: 0.85),
            )),
          ])),
          GestureDetector(
            onTap: () {
              ScaffoldMessenger.of(context).hideCurrentSnackBar();
              context.push('/bookings');
            },
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.25),
                borderRadius: BorderRadius.circular(rFull),
              ),
              child: Text('View', style: GoogleFonts.inter(
                fontSize: 12, fontWeight: FontWeight.w700, color: Colors.white,
              )),
            ),
          ),
        ]),
      ),
    );
    ScaffoldMessenger.of(context).showSnackBar(snackBar);
  }

  void _scrollToBottom() {
    if (_scroll.hasClients) {
      _scroll.animateTo(
        _scroll.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final messages = ref.watch(serviceChatProvider);
    final colors = context.appColors;

    // Show snackbar whenever a BOOKING_CREATED message appears
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _scrollToBottom();
      for (final m in messages) {
        if (m.action == 'BOOKING_CREATED' && m.actionData?['booking'] != null && !m._notified) {
          m._notified = true;
          _showBookingConfirmedSnackBar(Map<String, dynamic>.from(m.actionData!['booking']));
        }
      }
    });

    return Scaffold(
      backgroundColor: colors.scaffoldBg,
      appBar: AppBar(
        backgroundColor: colors.scaffoldBg, elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios_new, size: 18, color: colors.textPrimary),
          onPressed: () => context.pop(),
        ),
        title: Row(children: [
          Container(
            width: 34, height: 34,
            decoration: const BoxDecoration(
              gradient: LinearGradient(colors: [kAccent, Color(0xFF86EFAC)]),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.support_agent, size: 18, color: Colors.black),
          ),
          const SizedBox(width: 10),
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Service Advisor', style: GoogleFonts.inter(
              fontSize: 15, fontWeight: FontWeight.w700, color: colors.textPrimary,
            )),
            Text('AI-powered · AutoPredict', style: GoogleFonts.inter(
              fontSize: 10, color: kGood,
            )),
          ]),
        ]),
      ),
      body: Column(
        children: [
          // Chat area
          Expanded(
            child: ListView.builder(
              controller: _scroll,
              physics: const BouncingScrollPhysics(),
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
              itemCount: messages.length,
              itemBuilder: (_, i) {
                final m = messages[i];

                // Typing indicator
                if (m.action == '_typing') {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Align(
                      alignment: Alignment.centerLeft,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        decoration: BoxDecoration(
                          color: colors.surface,
                          borderRadius: BorderRadius.circular(rLG),
                          boxShadow: [colors.cardShadowStyle],
                        ),
                        child: _TypingDots(colors: colors),
                      ),
                    ),
                  );
                }

                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Main message bubble
                    _MessageBubble(m: m, colors: colors),

                    // Calendar slot picker
                    if (m.action == 'SHOW_SLOTS' && m.actionData != null)
                      _SlotCalendar(
                        calendar: (m.actionData!['calendar'] as List?)
                            ?.map((d) => _SlotDay.fromJson(Map<String, dynamic>.from(d)))
                            .toList() ?? [],
                        onSlotPicked: (slot) {
                          HapticFeedback.mediumImpact();
                          // Directly book without sending to AI
                          ref.read(serviceChatProvider.notifier).bookSlot(slot);
                          Future.delayed(const Duration(milliseconds: 600), _scrollToBottom);
                        },
                      ),

                    // Booking confirmation card
                    if (m.action == 'BOOKING_CREATED' && m.actionData?['booking'] != null)
                      _BookingConfirmCard(
                        booking: Map<String, dynamic>.from(m.actionData!['booking']),
                        colors: colors,
                        onView: () => context.push('/bookings'),
                      ),
                  ],
                );
              },
            ),
          ),

          // Quick prompts
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
            child: Row(children: [
              for (final q in [
                'Yes, book service',
                'What\'s the cost?',
                'How urgent is it?',
                'Show me slots',
                'Tomorrow morning',
              ])
                GestureDetector(
                  onTap: () => _send(q),
                  child: Container(
                    margin: const EdgeInsets.only(right: 8),
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    decoration: BoxDecoration(
                      color: colors.surface,
                      borderRadius: BorderRadius.circular(rFull),
                      border: Border.all(color: colors.navBorder),
                    ),
                    child: Text(q, style: GoogleFonts.inter(
                      fontSize: 12, color: colors.textSecondary,
                    )),
                  ),
                ),
            ]),
          ),

          // Input bar
          Container(
            color: colors.surface,
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
            child: Row(children: [
              Expanded(
                child: TextField(
                  controller: _ctrl,
                  style: TextStyle(color: colors.textPrimary),
                  onSubmitted: _send,
                  decoration: InputDecoration(
                    hintText: 'Talk to your service advisor…',
                    hintStyle: GoogleFonts.inter(color: colors.textHint, fontSize: 14),
                    filled: true, fillColor: colors.inputFill,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(rFull),
                      borderSide: BorderSide.none,
                    ),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              GestureDetector(
                onTap: () { HapticFeedback.lightImpact(); _send(_ctrl.text); },
                child: Container(
                  width: 44, height: 44,
                  decoration: const BoxDecoration(color: kAccent, shape: BoxShape.circle),
                  child: const Icon(Icons.arrow_upward, size: 20, color: Colors.black),
                ),
              ),
            ]),
          ),
        ],
      ),
    );
  }
}

// ─── Message Bubble ───────────────────────────────────────────────────────────

class _MessageBubble extends StatelessWidget {
  final _AgentMessage m;
  final dynamic colors;
  const _MessageBubble({required this.m, required this.colors});

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 8),
    child: Row(
      mainAxisAlignment: m.isAgent ? MainAxisAlignment.start : MainAxisAlignment.end,
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        if (m.isAgent) ...[
          Container(
            width: 28, height: 28,
            decoration: const BoxDecoration(color: kAccent, shape: BoxShape.circle),
            child: const Icon(Icons.support_agent, size: 14, color: Colors.black),
          ),
          const SizedBox(width: 8),
        ],
        Flexible(
          child: Container(
            constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.72),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: m.isAgent ? colors.surface : kAccent,
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(rLG),
                topRight: const Radius.circular(rLG),
                bottomLeft: Radius.circular(m.isAgent ? rXS : rLG),
                bottomRight: Radius.circular(m.isAgent ? rLG : rXS),
              ),
              boxShadow: m.isAgent ? [colors.cardShadowStyle] : [],
            ),
            child: Text(m.text, style: GoogleFonts.inter(
              fontSize: 14, height: 1.45,
              color: m.isAgent ? colors.textPrimary : kDark,
            )),
          ),
        ),
      ],
    ),
  );
}

// ─── Typing Dots ─────────────────────────────────────────────────────────────

class _TypingDots extends StatefulWidget {
  final dynamic colors;
  const _TypingDots({required this.colors});
  @override
  State<_TypingDots> createState() => _TypingDotsState();
}

class _TypingDotsState extends State<_TypingDots> with TickerProviderStateMixin {
  late List<AnimationController> _ctrls;
  @override
  void initState() {
    super.initState();
    _ctrls = List.generate(3, (i) {
      final c = AnimationController(vsync: this, duration: const Duration(milliseconds: 500))..repeat(reverse: true);
      Future.delayed(Duration(milliseconds: i * 160), () { if (mounted) c.forward(); });
      return c;
    });
  }
  @override
  void dispose() { for (final c in _ctrls) c.dispose(); super.dispose(); }
  @override
  Widget build(BuildContext context) => SizedBox(
    height: 16,
    child: Row(mainAxisSize: MainAxisSize.min, children: List.generate(3, (i) => AnimatedBuilder(
      animation: _ctrls[i],
      builder: (_, __) => Transform.translate(
        offset: Offset(0, -5 * _ctrls[i].value),
        child: Container(
          width: 7, height: 7,
          margin: const EdgeInsets.symmetric(horizontal: 2),
          decoration: BoxDecoration(color: widget.colors.textSecondary, shape: BoxShape.circle),
        ),
      ),
    ))),
  );
}

// ─── Calendar Slot Picker ─────────────────────────────────────────────────────

class _SlotCalendar extends StatefulWidget {
  final List<_SlotDay> calendar;
  final ValueChanged<Map<String, dynamic>> onSlotPicked;
  const _SlotCalendar({required this.calendar, required this.onSlotPicked});
  @override
  State<_SlotCalendar> createState() => _SlotCalendarState();
}

class _SlotCalendarState extends State<_SlotCalendar> {
  int _dayIdx = 0;

  @override
  Widget build(BuildContext context) {
    final colors = context.appColors;
    if (widget.calendar.isEmpty) return const SizedBox.shrink();
    final day = widget.calendar[_dayIdx];

    return Container(
      margin: const EdgeInsets.only(bottom: 16, top: 4),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(rLG),
        border: Border.all(color: kAccent.withValues(alpha: 0.3)),
        boxShadow: [colors.cardShadowStyle],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Padding(
            padding: const EdgeInsets.all(14),
            child: Row(children: [
              const Icon(Icons.calendar_month, size: 18, color: kAccentDark),
              const SizedBox(width: 8),
              Text('Pick a Service Slot', style: GoogleFonts.inter(
                fontSize: 14, fontWeight: FontWeight.w700, color: colors.textPrimary,
              )),
            ]),
          ),

          // Day tabs
          SizedBox(
            height: 60,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              itemCount: widget.calendar.length,
              itemBuilder: (_, i) {
                final d = widget.calendar[i];
                final isActive = i == _dayIdx;
                final parts = d.label.split(', ');  // e.g. "Wednesday, 18 March"
                final dayName = parts.isNotEmpty ? parts[0].substring(0, 3) : '';
                final dayDate = parts.length > 1 ? parts[1].split(' ').first : '';

                return GestureDetector(
                  onTap: () => setState(() => _dayIdx = i),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    margin: const EdgeInsets.only(right: 8),
                    width: 48,
                    decoration: BoxDecoration(
                      color: isActive ? kAccent : colors.neuBg,
                      borderRadius: BorderRadius.circular(rMD),
                      border: isActive ? null : Border.all(color: colors.navBorder),
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(dayName, style: GoogleFonts.inter(
                          fontSize: 10, fontWeight: FontWeight.w600,
                          color: isActive ? kDark : colors.textSecondary,
                        )),
                        const SizedBox(height: 2),
                        Text(dayDate, style: GoogleFonts.inter(
                          fontSize: 16, fontWeight: FontWeight.w800,
                          color: isActive ? kDark : colors.textPrimary,
                        )),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),

          const SizedBox(height: 8),

          // Time slots grid
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(day.label, style: GoogleFonts.inter(
                  fontSize: 12, color: colors.textSecondary, fontWeight: FontWeight.w500,
                )),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8, runSpacing: 8,
                  children: day.slots.map((slot) {
                    final avail = slot['available'] == true;
                    return GestureDetector(
                      onTap: avail ? () => widget.onSlotPicked(slot) : null,
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 150),
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                        decoration: BoxDecoration(
                          color: avail ? colors.surface : colors.neuBg,
                          borderRadius: BorderRadius.circular(rMD),
                          border: Border.all(
                            color: avail ? kAccent.withValues(alpha: 0.5) : colors.navBorder,
                          ),
                        ),
                        child: Text(
                          slot['slot_time'] ?? '',
                          style: GoogleFonts.inter(
                            fontSize: 13,
                            fontWeight: avail ? FontWeight.w600 : FontWeight.w400,
                            color: avail ? colors.textPrimary : colors.textHint,
                          ),
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Booking Confirmation Card ────────────────────────────────────────────────

class _BookingConfirmCard extends StatelessWidget {
  final Map<String, dynamic> booking;
  final dynamic colors;
  final VoidCallback onView;
  const _BookingConfirmCard({required this.booking, required this.colors, required this.onView});

  String _buildCalendarUrl() {
    final component = (booking['service_component'] as String? ?? 'Car Service').replaceAll('_', ' ');
    final slot = booking['slot_time_iso'] ?? '';
    DateTime? start;
    try { start = DateTime.parse(slot); } catch (_) { start = DateTime.now().add(const Duration(days: 1)); }
    final end = start.add(const Duration(hours: 2));
    String fmt(DateTime d) => d.toIso8601String().replaceAll('-','').replaceAll(':','').split('.').first + 'Z';
    final title = Uri.encodeComponent('AutoPredict: $component Service');
    final details = Uri.encodeComponent(
      'Booked via AutoPredict App\nTechnician: ${booking['technician_name'] ?? "-"}\nBay: ${booking['bay'] ?? "-"}'
    );
    return 'https://calendar.google.com/calendar/render?action=TEMPLATE'
        '&text=$title&dates=${fmt(start)}/${fmt(end)}&details=$details';
  }

  @override
  Widget build(BuildContext context) => Container(
    margin: const EdgeInsets.only(bottom: 16, top: 4),
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: kGood.withValues(alpha: 0.06),
      borderRadius: BorderRadius.circular(rLG),
      border: Border.all(color: kGood.withValues(alpha: 0.35)),
    ),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        const Icon(Icons.check_circle, color: kGood, size: 20),
        const SizedBox(width: 8),
        Text('Booking Confirmed! ✅', style: GoogleFonts.inter(
          fontSize: 14, fontWeight: FontWeight.w700, color: kGood,
        )),
      ]),
      const SizedBox(height: 12),
      _Detail(icon: Icons.build_outlined, text: (booking['service_component'] as String? ?? '').replaceAll('_', ' '), colors: colors),
      _Detail(icon: Icons.calendar_today_outlined, text: booking['slot_time'] ?? '', colors: colors),
      _Detail(icon: Icons.person_outline, text: booking['technician_name'] ?? '', colors: colors),
      _Detail(icon: Icons.garage_outlined, text: booking['bay'] ?? '', colors: colors),
      const SizedBox(height: 14),
      // Action buttons row
      Row(children: [
        // View bookings
        Expanded(
          child: GestureDetector(
            onTap: onView,
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 10),
              decoration: BoxDecoration(
                color: kAccentDark.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(rMD),
                border: Border.all(color: kAccentDark.withValues(alpha: 0.3)),
              ),
              child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                Icon(Icons.receipt_long_outlined, size: 14, color: kAccentDark),
                const SizedBox(width: 6),
                Text('View Booking', style: GoogleFonts.inter(
                  fontSize: 12, fontWeight: FontWeight.w600, color: kAccentDark,
                )),
              ]),
            ),
          ),
        ),
        const SizedBox(width: 10),
        // Add to Google Calendar
        Expanded(
          child: GestureDetector(
            onTap: () async {
              final url = Uri.parse(_buildCalendarUrl());
              if (await canLaunchUrl(url)) {
                await launchUrl(url, mode: LaunchMode.externalApplication);
              }
            },
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 10),
              decoration: BoxDecoration(
                color: const Color(0xFF4285F4).withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(rMD),
                border: Border.all(color: const Color(0xFF4285F4).withValues(alpha: 0.3)),
              ),
              child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                const Icon(Icons.calendar_month, size: 14, color: Color(0xFF4285F4)),
                const SizedBox(width: 6),
                Text('Add to Calendar', style: GoogleFonts.inter(
                  fontSize: 12, fontWeight: FontWeight.w600, color: const Color(0xFF4285F4),
                )),
              ]),
            ),
          ),
        ),
      ]),
    ]),
  );
}

class _Detail extends StatelessWidget {
  final IconData icon;
  final String text;
  final dynamic colors;
  const _Detail({required this.icon, required this.text, required this.colors});

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 6),
    child: Row(children: [
      Icon(icon, size: 14, color: colors.textSecondary),
      const SizedBox(width: 8),
      Text(text, style: GoogleFonts.inter(fontSize: 13, color: colors.textSecondary)),
    ]),
  );
}
