class ChatMessage {
  final String id;
  final bool isAI;
  final String text;
  final String? actionType; // 'BOOKING_CARD' | 'ALERT_CARD' | null
  final Map<String, dynamic>? actionData;
  final DateTime timestamp;
  final bool isTyping;

  const ChatMessage({
    required this.id,
    required this.isAI,
    required this.text,
    this.actionType,
    this.actionData,
    required this.timestamp,
    this.isTyping = false,
  });

  ChatMessage copyWith({String? text, bool? isTyping, String? actionType, Map<String, dynamic>? actionData}) =>
      ChatMessage(
        id: id, isAI: isAI,
        text: text ?? this.text,
        actionType: actionType ?? this.actionType,
        actionData: actionData ?? this.actionData,
        timestamp: timestamp,
        isTyping: isTyping ?? this.isTyping,
      );
}
