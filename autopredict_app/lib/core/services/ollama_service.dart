import 'dart:convert';
import 'package:dio/dio.dart';

/// Service to communicate with Ollama llama3:8b running at localhost:11434
class OllamaService {
  // ── ngrok tunnel URL ──────────────────────────────────────────────────────
  // 1. Run: ngrok http 11434
  // 2. Copy the https URL (e.g. https://abc123.ngrok-free.app)
  // 3. Paste it below (no trailing slash)
  // 4. Hot-restart the app (Shift+R in flutter run terminal)
  static const _baseUrl = 'https://discrepant-ungorged-adelaide.ngrok-free.dev';
  // ──────────────────────────────────────────────────────────────────────────
  static const _model   = 'llama3:8b';

  final Dio _dio = Dio(BaseOptions(
    baseUrl: _baseUrl,
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 60),
    headers: {
      'ngrok-skip-browser-warning': 'true', // required for ngrok tunnels
      'Content-Type': 'application/json',
    },
  ));

  /// Send a chat message with vehicle context injected into system prompt.
  /// Returns the full response text.
  Future<String> chat({
    required String userMessage,
    required Map<String, dynamic> vehicleContext,
    List<Map<String, String>> history = const [],
  }) async {
    final systemPrompt = _buildSystemPrompt(vehicleContext);

    final messages = [
      {'role': 'system', 'content': systemPrompt},
      ...history,
      {'role': 'user', 'content': userMessage},
    ];

    try {
      final response = await _dio.post('/api/chat', data: {
        'model': _model,
        'messages': messages,
        'stream': false,
        'options': {'temperature': 0.7, 'num_predict': 256},
      });

      final data = response.data;
      if (data is Map) {
        return data['message']?['content']?.toString().trim() ??
            'Sorry, I could not process that.';
      }
      return 'Sorry, unexpected response format.';
    } catch (e) {
      return 'AI service is offline. Please ensure Ollama is running on port 11434.';
    }
  }

  /// Stream a response token-by-token.
  Stream<String> chatStream({
    required String userMessage,
    required Map<String, dynamic> vehicleContext,
    List<Map<String, String>> history = const [],
  }) async* {
    final systemPrompt = _buildSystemPrompt(vehicleContext);
    final messages = [
      {'role': 'system', 'content': systemPrompt},
      ...history,
      {'role': 'user', 'content': userMessage},
    ];

    try {
      final response = await _dio.post<ResponseBody>(
        '/api/chat',
        data: json.encode({
          'model': _model,
          'messages': messages,
          'stream': true,
          'options': {'temperature': 0.7, 'num_predict': 256},
        }),
        options: Options(responseType: ResponseType.stream),
      );

      await for (final chunk in response.data!.stream) {
        final text = utf8.decode(chunk);
        for (final line in text.split('\n')) {
          if (line.trim().isEmpty) continue;
          try {
            final json_ = json.decode(line) as Map;
            final token = json_['message']?['content']?.toString() ?? '';
            if (token.isNotEmpty) yield token;
            if (json_['done'] == true) return;
          } catch (_) {}
        }
      }
    } catch (e) {
      yield '\n\n[AI offline — ensure Ollama is running]';
    }
  }

  String _buildSystemPrompt(Map<String, dynamic> ctx) {
    return '''You are AutoPredict AI, an expert vehicle diagnostics assistant.
You help drivers understand their vehicle health, diagnose issues, and book service appointments.

CURRENT VEHICLE DATA:
- Speed: ${ctx['speed']?.toStringAsFixed(1) ?? '0'} mph
- RPM: ${ctx['rpm']?.toStringAsFixed(0) ?? '0'}
- Coolant Temp: ${ctx['coolantTemp']?.toStringAsFixed(1) ?? '0'}°C
- Fuel Level: ${ctx['fuel']?.toStringAsFixed(1) ?? '0'}%
- Battery Voltage: ${ctx['voltage']?.toStringAsFixed(2) ?? '12.6'}V
- Engine Status: ${ctx['engineStatus'] ?? 'idle'}
- DTC Codes: ${(ctx['dtcCodes'] as List?)?.join(', ') ?? 'None'}

DIAGNOSTICS:
- Brake Pads: 2.1mm (CRITICAL — replace immediately)
- Battery: 11.8V (WARNING)
- Coolant System: 88°C (GOOD)
- Tires: FL ${ctx['tyrePressure'] ?? '31.5'} PSI (WARNING — low)

Keep responses concise (2-3 sentences max). If the user wants to book a service, 
end your response with ACTION:SHOW_BOOKING for brake pads, or ACTION:SHOW_ALERT for critical issues.''';
  }
}
