import 'package:dio/dio.dart';

/// REST + data helpers for the FastAPI backend at localhost:8001
class ApiService {
  // Use PC's LAN IP so physical device can reach the FastAPI backend.
  // Emulator alternative: 'http://10.0.2.2:8001/api'
  static const _base = 'http://192.168.0.199:8001/api';
  static const _vehicleId = 'VEH001'; // default vehicle for the app

  final Dio _dio = Dio(BaseOptions(
    baseUrl: _base,
    connectTimeout: const Duration(seconds: 8),
    receiveTimeout: const Duration(seconds: 15),
  ));

  // ── Vehicles ─────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> getVehicle([String? id]) async {
    try {
      final r = await _dio.get('/vehicles/${id ?? _vehicleId}');
      return r.data as Map<String, dynamic>;
    } catch (_) {
      return _mockVehicle();
    }
  }

  Future<List<Map<String, dynamic>>> getAllVehicles() async {
    try {
      final r = await _dio.get('/vehicles');
      return List<Map<String, dynamic>>.from(r.data as List);
    } catch (_) {
      return [_mockVehicle()];
    }
  }

  // ── Bookings ─────────────────────────────────────────────────────────────
  Future<List<Map<String, dynamic>>> getBookings() async {
    try {
      final r = await _dio.get('/bookings');
      return List<Map<String, dynamic>>.from(r.data as List);
    } catch (_) {
      return _mockBookings();
    }
  }

  Future<List<Map<String, dynamic>>> getAvailableSlots(String date) async {
    try {
      final r = await _dio.get('/availability', queryParameters: {'date': date});
      final slots = r.data['slots'] as List;
      return slots
          .where((s) => s['available'] == true)
          .map((s) => Map<String, dynamic>.from(s as Map))
          .toList();
    } catch (_) {
      return _mockSlots();
    }
  }

  Future<Map<String, dynamic>> createBooking(Map<String, dynamic> body) async {
    try {
      final r = await _dio.post('/bookings', data: body);
      return r.data as Map<String, dynamic>;
    } catch (_) {
      return {'booking_id': 'BK-LOCAL-001', 'status': 'CONFIRMED', ...body};
    }
  }

  Future<void> cancelBooking(String bookingId) async {
    try {
      await _dio.delete('/bookings/$bookingId');
    } catch (_) {}
  }

  // ── Dashboard / Alerts ────────────────────────────────────────────────────
  Future<Map<String, dynamic>> getDashboardSummary() async {
    try {
      final r = await _dio.get('/dashboard/summary');
      return r.data as Map<String, dynamic>;
    } catch (_) {
      return {'total_vehicles': 1, 'critical': 1, 'healthy': 0};
    }
  }

  // ── Analytics ─────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> getFleetAnalytics() async {
    try {
      final r = await _dio.get('/analytics/fleet');
      return r.data as Map<String, dynamic>;
    } catch (_) {
      return {};
    }
  }

  Future<Map<String, dynamic>> getMonthlyAnalytics() async {
    try {
      final r = await _dio.get('/analytics/monthly');
      return r.data as Map<String, dynamic>;
    } catch (_) {
      return {'months': []};
    }
  }

  // ── Service Chat Agent ────────────────────────────────────────────────────
  Future<Map<String, dynamic>> serviceChat({
    required String message,
    required String vehicleId,
    required List<Map<String, String>> history,
    Map<String, dynamic> vehicleContext = const {},
  }) async {
    try {
      final r = await _dio.post(
        '/chat',
        data: {
          'message': message,
          'vehicle_id': vehicleId,
          'history': history,
          'vehicle_context': vehicleContext,
        },
        options: Options(
          sendTimeout: const Duration(seconds: 30),
          receiveTimeout: const Duration(seconds: 35),
        ),
      );
      return Map<String, dynamic>.from(r.data as Map);
    } catch (e) {
      // Offline fallback — simulate first diagnosis message
      return _mockAgentReply(message, history.length);
    }
  }

  Map<String, dynamic> _mockAgentReply(String message, int turn) {
    if (turn == 0) {
      return {
        'reply': '👋 Hi! I\'ve been monitoring your Toyota Camry using live sensor data. '
            'Our AI has detected your **brake pads** are critically worn — only ~2.1mm left (safe minimum is 3mm). '
            'This was flagged with 88% confidence. Would you like to schedule a brake service? '
            'It\'s a quick 90-minute job.',
        'action': null,
        'action_data': {},
      };
    }
    final lower = message.toLowerCase();
    if (lower.contains('yes') || lower.contains('book') || lower.contains('schedule') || lower.contains('ok')) {
      return {
        'reply': 'Great! Let me pull up the available service slots for you.',
        'action': 'SHOW_SLOTS',
        'action_data': {
          'calendar': _mockCalendar(),
        },
      };
    }
    if (lower.contains('cost') || lower.contains('price') || lower.contains('how much')) {
      return {
        'reply': 'Brake pad replacement typically costs ₹2,500–₹4,000 for your Camry. '
            'This includes labour and OEM-quality parts. Shall I book a slot?',
        'action': null,
        'action_data': {},
      };
    }
    return {
      'reply': 'I understand. Your safety is the priority — the brake pads really do need attention soon. '
          'Would you like me to find the earliest available slot this week?',
      'action': null,
      'action_data': {},
    };
  }

  List<Map<String, dynamic>> _mockCalendar() {
    final now = DateTime.now();
    return List.generate(7, (dayOffset) {
      final day = now.add(Duration(days: dayOffset));
      final dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
      final abbrMonths = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      final label = '${dayNames[day.weekday - 1]}, ${day.day} ${abbrMonths[day.month - 1]}';
      return {
        'date': '${day.year}-${day.month.toString().padLeft(2, '0')}-${day.day.toString().padLeft(2, '0')}',
        'label': label,
        'slots': List.generate(8, (h) {
          final hour = 9 + h;
          final t = day.copyWith(hour: hour, minute: 0, second: 0);
          final timeStr = hour < 12
              ? '${hour.toString().padLeft(2, '0')}:00 AM'
              : hour == 12
                  ? '12:00 PM'
                  : '${(hour - 12).toString().padLeft(2, '0')}:00 PM';
          return {
            'slot_time': timeStr,
            'slot_time_iso': t.toIso8601String(),
            'date_label': '${dayNames[day.weekday - 1].substring(0, 3)}, ${day.day} ${abbrMonths[day.month - 1]}',
            'available': h != 2 && h != 5, // simulate 2 booked slots
          };
        }),
      };
    });
  }

  // ── Fallback mocks (when backend offline) ─────────────────────────────────
  Map<String, dynamic> _mockVehicle() => {
    'vehicle_id': _vehicleId,
    'make': 'Toyota',
    'model': 'Camry',
    'year': 2021,
    'health_score': 0.72,
    'failure_probability': 0.28,
    'priority': 'P1',
    'diagnosis': {
      'status': 'completed',
      'severity': 'warning',
      'predicted_component': 'brake_pads',
      'rul_days': 12,
      'confidence': 0.88,
    },
  };

  List<Map<String, dynamic>> _mockBookings() => [
    {
      'booking_id': 'BK20250317-0001',
      'vehicle_id': _vehicleId,
      'service_component': 'brake_pads',
      'slot_time': 'Tomorrow · 10:00 AM',
      'technician_name': 'Rajesh Kumar',
      'bay': 'BAY-A',
      'priority': 'P1',
      'status': 'CONFIRMED',
    },
  ];

  List<Map<String, dynamic>> _mockSlots() => [
    {'slot_time': '09:00 AM', 'slot_time_iso': '2025-03-18T09:00:00', 'available': true},
    {'slot_time': '10:00 AM', 'slot_time_iso': '2025-03-18T10:00:00', 'available': true},
    {'slot_time': '11:00 AM', 'slot_time_iso': '2025-03-18T11:00:00', 'available': true},
    {'slot_time': '02:00 PM', 'slot_time_iso': '2025-03-18T14:00:00', 'available': true},
    {'slot_time': '03:00 PM', 'slot_time_iso': '2025-03-18T15:00:00', 'available': true},
  ];
}
