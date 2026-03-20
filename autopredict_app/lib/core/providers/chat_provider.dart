import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/chat_message.dart';
import '../services/ollama_service.dart';
import 'vehicle_provider.dart';
import 'booking_provider.dart';

final _ollama = OllamaService();

class ChatNotifier extends StateNotifier<List<ChatMessage>> {
  final Ref _ref;

  ChatNotifier(this._ref) : super([
    ChatMessage(
      id: 'init',
      isAI: true,
      text: "Hi! I'm AutoPredict AI. I've analysed your vehicle — your brake pads are at 2.1mm, which is critical. Want me to find you a service slot?",
      timestamp: DateTime.now(),
    ),
  ]);

  final List<Map<String, String>> _history = [];

  Future<void> sendMessage(String text) async {
    if (text.trim().isEmpty) return;

    // Add user message
    final userMsg = ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      isAI: false,
      text: text,
      timestamp: DateTime.now(),
    );
    state = [...state, userMsg];
    _history.add({'role': 'user', 'content': text});

    // Add typing indicator
    final typingId = '${DateTime.now().millisecondsSinceEpoch}_typing';
    state = [...state, ChatMessage(
      id: typingId, isAI: true, text: '...', timestamp: DateTime.now(), isTyping: true,
    )];

    // Get current vehicle context
    final vehicle = _ref.read(vehicleProvider);
    final bookingsList = _ref.read(bookingProvider).value ?? [];
    final activeBookings = bookingsList.where((b) => b['status'] != 'CANCELLED').toList();
    final hasBooking = activeBookings.isNotEmpty;
    final bookingDesc = hasBooking ? "${activeBookings.first['service_component']} at ${activeBookings.first['slot_time']}" : "None";

    final ctx = {
      'speed': vehicle.speedMph,
      'rpm': vehicle.rpm,
      'coolantTemp': vehicle.coolantTempC,
      'fuel': vehicle.fuelLevelPct,
      'voltage': vehicle.batteryVoltage,
      'engineStatus': vehicle.engineStatus,
      'dtcCodes': vehicle.dtcCodes,
      'tyrePressure': vehicle.tyrePressureFl.toStringAsFixed(1),
      'activeBooking': bookingDesc,
    };

    // Stream AI response
    final aiId = '${DateTime.now().millisecondsSinceEpoch}_ai';
    String accumulated = '';

    // Replace typing indicator
    state = state.where((m) => m.id != typingId).toList();
    state = [...state, ChatMessage(
      id: aiId, isAI: true, text: '', timestamp: DateTime.now(),
    )];

    await for (final token in _ollama.chatStream(
      userMessage: text,
      vehicleContext: ctx,
      history: _history,
    )) {
      accumulated += token;
      state = [
        ...state.where((m) => m.id != aiId),
        ChatMessage(
          id: aiId, isAI: true, text: accumulated, timestamp: DateTime.now(),
        ),
      ];
    }

    // Check if AI wants to trigger an action card
    String? actionType;
    Map<String, dynamic>? actionData;

    if (accumulated.contains('ACTION:SHOW_BOOKING') && !hasBooking) {
      actionType = 'BOOKING_CARD';
      actionData = {
        'service': 'Brake Pads Service',
        'slot': 'Tomorrow · 10:00 AM',
        'technician': 'Rajesh Kumar',
        'bay': 'Bay A',
      };
    } else if (accumulated.contains('ACTION:SHOW_ALERT')) {
      actionType = 'ALERT_CARD';
      actionData = {'component': 'Brake Pads', 'urgency': 'CRITICAL'};
    }

    // Update message with action if needed
    final cleanText = accumulated
        .replaceAll('ACTION:SHOW_BOOKING', '')
        .replaceAll('ACTION:SHOW_ALERT', '')
        .trim();

    state = [
      ...state.where((m) => m.id != aiId),
      ChatMessage(
        id: aiId,
        isAI: true,
        text: cleanText,
        timestamp: DateTime.now(),
        actionType: actionType,
        actionData: actionData,
      ),
    ];

    _history.add({'role': 'assistant', 'content': cleanText});
  }

  void clearChat() {
    _history.clear();
    state = [
      ChatMessage(
        id: 'init_${DateTime.now().millisecondsSinceEpoch}',
        isAI: true,
        text: "Chat cleared. How can I help with your vehicle?",
        timestamp: DateTime.now(),
      ),
    ];
  }

  void clearAction(String messageId) {
    state = state.map((m) {
      if (m.id == messageId) {
        return ChatMessage(
          id: m.id,
          isAI: m.isAI,
          text: m.text,
          timestamp: m.timestamp,
        );
      }
      return m;
    }).toList();
  }

  void confirmBookingAction(String messageId, Map<String, dynamic> booking) {
    state = state.map((m) {
      if (m.id == messageId) {
        return ChatMessage(
          id: m.id,
          isAI: m.isAI,
          text: 'Great news! ✅ Your service appointment has been confirmed.',
          timestamp: m.timestamp,
          actionType: 'BOOKING_CREATED',
          actionData: {'booking': booking},
        );
      }
      return m;
    }).toList();
  }
}

final chatProvider = StateNotifierProvider<ChatNotifier, List<ChatMessage>>(
  (ref) => ChatNotifier(ref),
);
