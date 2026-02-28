import 'package:flutter/material.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/typography.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});
  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _ctrl    = TextEditingController();
  final _scroll  = ScrollController();
  final List<_Msg> _messages = [
    _Msg(isAI: true,
      text: 'Hi! I\'ve analysed your vehicle. Your brake pads are at 2.1mm — that\'s critical. Want me to book a service?',
      action: null),
  ];

  void _send(String text) {
    if (text.trim().isEmpty) return;
    setState(() {
      _messages.add(_Msg(isAI: false, text: text, action: null));
      _ctrl.clear();
    });
    // Simulate AI reply
    Future.delayed(const Duration(milliseconds: 800), () {
      if (!mounted) return;
      setState(() => _messages.add(const _Msg(
        isAI: true,
        text: 'I found a slot tomorrow at 10:00 AM — Bay 3, Rajesh Kumar. Shall I confirm?',
        action: 'SHOW_BOOKING_CARD',
      )));
      Future.delayed(const Duration(milliseconds: 100), () =>
        _scroll.animateTo(_scroll.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300), curve: Curves.easeOut));
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      appBar: AppBar(
        backgroundColor: kBg, elevation: 0,
        title: Text('AutoPredict AI', style: kSubtitle()),
        actions: [
          IconButton(icon: const Icon(Icons.mic_none, color: Colors.grey), onPressed: () {}),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scroll,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (_, i) => _BubbleWidget(msg: _messages[i]),
            ),
          ),
          // Input bar
          Container(
            color: kSurface,
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _ctrl,
                    decoration: InputDecoration(
                      hintText: 'Type a message…',
                      hintStyle: kBody(),
                      filled: true, fillColor: kBg,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(rFull), borderSide: BorderSide.none),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                    ),
                    onSubmitted: _send,
                  ),
                ),
                const SizedBox(width: 10),
                GestureDetector(
                  onTap: () => _send(_ctrl.text),
                  child: Container(
                    width: 44, height: 44,
                    decoration: BoxDecoration(color: kAccent, shape: BoxShape.circle),
                    child: const Icon(Icons.arrow_upward, size: 20, color: Colors.black),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Msg {
  final bool isAI;
  final String text;
  final String? action;
  const _Msg({required this.isAI, required this.text, required this.action});
}

class _BubbleWidget extends StatelessWidget {
  final _Msg msg;
  const _BubbleWidget({super.key, required this.msg});

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
              constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.72),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: msg.isAI ? kSurface : kAccent,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(rLG),
                  topRight: const Radius.circular(rLG),
                  bottomLeft: Radius.circular(msg.isAI ? rXS : rLG),
                  bottomRight: Radius.circular(msg.isAI ? rLG : rXS),
                ),
                boxShadow: msg.isAI ? const [cardShadow] : [],
              ),
              child: Text(msg.text, style: kBody(color: msg.isAI ? kDark : kDark)),
            ),
            // Booking card action
            if (msg.isAI && msg.action == 'SHOW_BOOKING_CARD')
              Container(
                margin: const EdgeInsets.only(top: 8),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: kSurface, borderRadius: BorderRadius.circular(rLG),
                  border: Border.all(color: kAccent, width: 1.5),
                  boxShadow: const [cardShadow],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _InfoRow(icon: Icons.calendar_today_outlined, text: 'Tomorrow · 10:00 AM'),
                    _InfoRow(icon: Icons.location_on_outlined, text: 'Bay 3 · Rajesh Kumar'),
                    _InfoRow(icon: Icons.build_outlined, text: 'Brake Pads Service'),
                    const SizedBox(height: 10),
                    Container(
                      width: double.infinity, height: 40,
                      decoration: BoxDecoration(color: kAccent, borderRadius: BorderRadius.circular(rMD)),
                      child: Center(child: Text('Confirm Booking', style: kLabel(color: kDark))),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String text;
  const _InfoRow({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 6),
    child: Row(children: [
      Icon(icon, size: 14, color: kMid),
      const SizedBox(width: 8),
      Text(text, style: kBody()),
    ]),
  );
}
