import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/colors.dart';
import '../../core/models/chat_message.dart';
import '../../core/providers/chat_provider.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});
  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _ctrl   = TextEditingController();
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
    ref.read(chatProvider.notifier).sendMessage(text);
    Future.delayed(const Duration(milliseconds: 400), _scrollToBottom);
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
    final messages = ref.watch(chatProvider);
    final colors = context.appColors;

    // Auto-scroll when messages update
    WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());

    return Scaffold(
      backgroundColor: colors.scaffoldBg,
      appBar: AppBar(
        backgroundColor: colors.scaffoldBg, elevation: 0,
        title: Row(children: [
          Container(
            width: 34, height: 34,
            decoration: const BoxDecoration(color: kAccent, shape: BoxShape.circle),
            child: const Icon(Icons.psychology, size: 18, color: Colors.black),
          ),
          const SizedBox(width: 10),
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('AutoPredict AI', style: GoogleFonts.inter(
              fontSize: 15, fontWeight: FontWeight.w700, color: colors.textPrimary,
            )),
            Text('llama3 · Ollama', style: GoogleFonts.inter(
              fontSize: 10, color: colors.textSecondary,
            )),
          ]),
        ]),
        actions: [
          IconButton(
            icon: Icon(Icons.delete_outline, color: colors.textSecondary, size: 20),
            onPressed: () => ref.read(chatProvider.notifier).clearChat(),
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scroll,
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
              itemCount: messages.length,
              itemBuilder: (_, i) {
                final msg = messages[i];
                return _BubbleWidget(
                  msg: msg,
                  colors: colors,
                  onBookingConfirm: () async {
                    final result = await context.push<dynamic>('/book-new');
                    if (result != null && result is Map) {
                      ref.read(chatProvider.notifier).confirmBookingAction(msg.id, Map<String, dynamic>.from(result));
                    }
                  },
                );
              },
            ),
          ),
          // Suggestion chips
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
            child: Row(children: [
              for (final q in [
                'How are my brakes?',
                'Book a service',
                'Check battery',
                'Tire pressure?',
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
                    hintText: 'Ask about your vehicle…',
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
                onTap: () => _send(_ctrl.text),
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

class _BubbleWidget extends StatelessWidget {
  final ChatMessage msg;
  final dynamic colors;
  final VoidCallback onBookingConfirm;
  const _BubbleWidget({required this.msg, required this.colors, required this.onBookingConfirm});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Align(
        alignment: msg.isAI ? Alignment.centerLeft : Alignment.centerRight,
        child: Column(
          crossAxisAlignment: msg.isAI ? CrossAxisAlignment.start : CrossAxisAlignment.end,
          children: [
            Container(
              constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: msg.isAI ? colors.surface : kAccent,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(rLG),
                  topRight: const Radius.circular(rLG),
                  bottomLeft: Radius.circular(msg.isAI ? rXS : rLG),
                  bottomRight: Radius.circular(msg.isAI ? rLG : rXS),
                ),
                boxShadow: msg.isAI ? [colors.cardShadowStyle] : [],
              ),
              child: msg.isTyping
                  ? _TypingIndicator(colors: colors)
                  : Text(
                      msg.text,
                      style: GoogleFonts.inter(
                        fontSize: 14,
                        color: msg.isAI ? colors.textPrimary : kDark,
                        height: 1.45,
                      ),
                    ),
            ),
            // Action cards
            if (msg.actionType == 'BOOKING_CARD' && msg.actionData != null) ...[
              const SizedBox(height: 8),
              _BookingCard(data: msg.actionData!, colors: colors, onConfirm: onBookingConfirm),
            ],
            if (msg.actionType == 'ALERT_CARD' && msg.actionData != null) ...[
              const SizedBox(height: 8),
              _AlertCard(data: msg.actionData!, colors: colors),
            ],
            if (msg.actionType == 'BOOKING_CREATED' && msg.actionData?['booking'] != null) ...[
              const SizedBox(height: 8),
              _BookingConfirmCard(
                booking: Map<String, dynamic>.from(msg.actionData!['booking']),
                colors: colors,
                onView: () => context.push('/bookings'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _BookingConfirmCard extends StatelessWidget {
  final Map<String, dynamic> booking;
  final dynamic colors;
  final VoidCallback onView;

  const _BookingConfirmCard({required this.booking, required this.colors, required this.onView});

  @override
  Widget build(BuildContext context) => Container(
    margin: const EdgeInsets.only(top: 4),
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: kGood.withValues(alpha: 0.06),
      borderRadius: BorderRadius.circular(rLG),
      border: Border.all(color: kGood.withValues(alpha: 0.35)),
    ),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        const Icon(Icons.check_circle, color: kGood, size: 18),
        const SizedBox(width: 8),
        Text('Booking Confirmed! ✅', style: GoogleFonts.inter(
          fontSize: 13, fontWeight: FontWeight.w700, color: kGood,
        )),
      ]),
      const SizedBox(height: 12),
      _Row(icon: Icons.build_outlined, text: (booking['service_component'] as String? ?? '').replaceAll('_', ' '), colors: colors),
      _Row(icon: Icons.calendar_today_outlined, text: booking['slot_time'] ?? '', colors: colors),
      _Row(icon: Icons.person_outline, text: booking['technician_name'] ?? '', colors: colors),
      _Row(icon: Icons.garage_outlined, text: booking['bay'] ?? '', colors: colors),
      const SizedBox(height: 10),
      GestureDetector(
        onTap: () { HapticFeedback.mediumImpact(); onView(); },
        child: Container(
          width: double.infinity, height: 40,
          decoration: BoxDecoration(
            color: kAccentDark.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(rMD),
            border: Border.all(color: kAccentDark.withValues(alpha: 0.3)),
          ),
          child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
            Icon(Icons.receipt_long_outlined, size: 14, color: kAccentDark),
            const SizedBox(width: 6),
            Text('View Bookings', style: GoogleFonts.inter(
              fontSize: 13, fontWeight: FontWeight.w600, color: kAccentDark,
            )),
          ]),
        ),
      ),
    ]),
  );
}

class _TypingIndicator extends StatefulWidget {
  final dynamic colors;
  const _TypingIndicator({required this.colors});
  @override
  State<_TypingIndicator> createState() => _TypingIndicatorState();
}

class _TypingIndicatorState extends State<_TypingIndicator>
    with TickerProviderStateMixin {
  late List<AnimationController> _ctrls;
  late List<Animation<double>> _anims;

  @override
  void initState() {
    super.initState();
    _ctrls = List.generate(3, (i) => AnimationController(
      vsync: this, duration: const Duration(milliseconds: 600),
    )..repeat(reverse: true));
    _anims = List.generate(3, (i) {
      Future.delayed(Duration(milliseconds: i * 150), () {
        if (mounted) _ctrls[i].forward();
      });
      return Tween<double>(begin: 0, end: -6).animate(
        CurvedAnimation(parent: _ctrls[i], curve: Curves.easeInOut),
      );
    });
  }

  @override
  void dispose() {
    for (final c in _ctrls) c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 20,
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: List.generate(3, (i) => AnimatedBuilder(
          animation: _anims[i],
          builder: (_, __) => Transform.translate(
            offset: Offset(0, _anims[i].value),
            child: Container(
              width: 7, height: 7,
              margin: const EdgeInsets.symmetric(horizontal: 2.5),
              decoration: BoxDecoration(
                color: widget.colors.textSecondary,
                shape: BoxShape.circle,
              ),
            ),
          ),
        )),
      ),
    );
  }
}

class _BookingCard extends StatelessWidget {
  final Map<String, dynamic> data;
  final dynamic colors;
  final VoidCallback onConfirm;
  const _BookingCard({required this.data, required this.colors, required this.onConfirm});

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: colors.surface,
      borderRadius: BorderRadius.circular(rLG),
      border: Border.all(color: kAccent, width: 1.5),
      boxShadow: [colors.cardShadowStyle],
    ),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      _Row(icon: Icons.build_outlined, text: data['service'] ?? 'Service', colors: colors),
      _Row(icon: Icons.calendar_today_outlined, text: data['slot'] ?? 'TBD', colors: colors),
      _Row(icon: Icons.person_outline, text: data['technician'] ?? 'TBD', colors: colors),
      _Row(icon: Icons.garage_outlined, text: data['bay'] ?? 'TBD', colors: colors),
      const SizedBox(height: 10),
      GestureDetector(
        onTap: () { HapticFeedback.mediumImpact(); onConfirm(); },
        child: Container(
          width: double.infinity, height: 40,
          decoration: BoxDecoration(color: kAccent, borderRadius: BorderRadius.circular(rMD)),
          child: Center(child: Text('Confirm Booking',
              style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w700, color: kDark))),
        ),
      ),
    ]),
  );
}

class _AlertCard extends StatelessWidget {
  final Map<String, dynamic> data;
  final dynamic colors;
  const _AlertCard({required this.data, required this.colors});

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: kDanger.withValues(alpha: 0.08),
      borderRadius: BorderRadius.circular(rLG),
      border: Border.all(color: kDanger.withValues(alpha: 0.4)),
    ),
    child: Row(children: [
      const Icon(Icons.warning_amber_rounded, color: kDanger, size: 20),
      const SizedBox(width: 10),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('${data['component'] ?? 'Component'} Alert',
            style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w700, color: kDanger)),
        Text('Urgency: ${data['urgency'] ?? 'HIGH'}',
            style: GoogleFonts.inter(fontSize: 12, color: kDanger.withValues(alpha: 0.7))),
      ])),
    ]),
  );
}

class _Row extends StatelessWidget {
  final IconData icon;
  final String text;
  final dynamic colors;
  const _Row({required this.icon, required this.text, required this.colors});

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
