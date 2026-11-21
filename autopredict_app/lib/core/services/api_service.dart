import 'package:dio/dio.dart';

import 'session.dart';

/// Thrown when an API call fails in a way the user should see.
class ApiException implements Exception {
  final String message;
  final int? statusCode;
  ApiException(this.message, [this.statusCode]);
  @override
  String toString() => message;
}

/// REST client for the AutoPredict API.
///
/// Server address is set at build time:
///   flutter run --dart-define=API_BASE_URL=http://192.168.1.20:8001/api
/// Default targets the Android emulator's alias for the host machine.
class ApiService {
  static const _base = String.fromEnvironment('API_BASE_URL', defaultValue: 'http://10.0.2.2:8001/api');

  // One client for the whole app (auth header + token refresh live here).
  static final Dio _dio = _buildClient();

  static Dio _buildClient() {
    final dio = Dio(BaseOptions(
      baseUrl: _base,
      connectTimeout: const Duration(seconds: 8),
      receiveTimeout: const Duration(seconds: 15),
    ));
    dio.interceptors.add(QueuedInterceptorsWrapper(
      onRequest: (options, handler) {
        final token = Session.accessToken;
        if (token != null) options.headers['Authorization'] = 'Bearer $token';
        handler.next(options);
      },
      onError: (error, handler) async {
        final req = error.requestOptions;
        final isAuthCall = req.path.startsWith('/auth/');
        if (error.response?.statusCode == 401 && !isAuthCall && req.extra['retried'] != true) {
          if (await _refresh()) {
            req.extra['retried'] = true;
            req.headers['Authorization'] = 'Bearer ${Session.accessToken}';
            try {
              return handler.resolve(await dio.fetch(req));
            } on DioException catch (e) {
              return handler.next(e);
            }
          }
          await Session.clear(); // refresh failed: the router sends the user to /login
        }
        handler.next(error);
      },
    ));
    return dio;
  }

  static Future<bool> _refresh() async {
    final refresh = Session.refreshToken;
    if (refresh == null) return false;
    try {
      final r = await Dio(BaseOptions(baseUrl: _base)).post('/auth/refresh', data: {'refresh_token': refresh});
      await Session.saveTokens(Map<String, dynamic>.from(r.data as Map));
      return true;
    } catch (_) {
      return false;
    }
  }

  static String _message(Object e, String fallback) {
    if (e is DioException) {
      final detail = (e.response?.data is Map) ? (e.response!.data as Map)['detail'] : null;
      if (detail is String) return detail;
      if (e.type == DioExceptionType.connectionTimeout || e.type == DioExceptionType.connectionError) {
        return 'Can\'t reach the AutoPredict server. Check your connection.';
      }
    }
    return fallback;
  }

  /// The signed-in owner's selected car.
  String get _vehicleId => Session.vehicleId ?? '';

  // ── Auth (owner phone + one-time code) ────────────────────────────────────
  /// Returns the server response; in development it includes `debug_otp`.
  Future<Map<String, dynamic>> sendOtp(String phone) async {
    try {
      final r = await _dio.post('/auth/otp/send', data: {'phone': phone});
      return Map<String, dynamic>.from(r.data as Map);
    } catch (e) {
      throw ApiException(_message(e, 'Could not send the code. Try again.'));
    }
  }

  /// Verifies the code, stores the session and selects the owner's first car.
  Future<void> verifyOtp(String phone, String code) async {
    try {
      final r = await _dio.post('/auth/otp/verify', data: {'phone': phone, 'otp': code});
      await Session.saveTokens(Map<String, dynamic>.from(r.data as Map));
      final cars = await _dio.get('/me/vehicles');
      final list = List<Map<String, dynamic>>.from(cars.data as List);
      await Session.selectVehicle(list.isNotEmpty ? list.first['vehicle_id'] as String : null);
    } catch (e) {
      throw ApiException(_message(e, 'Could not verify the code. Try again.'));
    }
  }

  Future<void> logout() async {
    final refresh = Session.refreshToken;
    if (refresh != null) {
      try {
        await _dio.post('/auth/logout', data: {'refresh_token': refresh});
      } catch (_) {
        // Token already invalid server-side; clearing locally is enough.
      }
    }
    await Session.clear();
  }

  // ── Vehicles ─────────────────────────────────────────────────────────────
  /// The signed-in owner's selected car with its per-part assessment.
  /// Throws [ApiException] instead of falling back to sample data.
  Future<Map<String, dynamic>> getVehicleDetail() async {
    if (_vehicleId.isEmpty) throw ApiException('No vehicle linked to this account yet.');
    try {
      final r = await _dio.get('/vehicles/$_vehicleId');
      return Map<String, dynamic>.from(r.data as Map);
    } catch (e) {
      throw ApiException(_message(e, 'Could not load your car\'s health.'));
    }
  }

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

  /// Free start times on [date] (YYYY-MM-DD) for a job type, from the workshop calendar.
  Future<List<Map<String, dynamic>>> getAvailableSlots(String date, {String component = 'Full Service'}) async {
    try {
      final r = await _dio.get('/availability', queryParameters: {'date': date, 'component': component});
      final slots = r.data['slots'] as List;
      return slots
          .where((s) => s['available'] == true)
          .map((s) => Map<String, dynamic>.from(s as Map))
          .toList();
    } catch (e) {
      throw ApiException(_message(e, 'Could not load free slots.'));
    }
  }

  /// Creates a booking for the signed-in owner's car. Throws [ApiException] on failure;
  /// never returns a pretend confirmation.
  Future<Map<String, dynamic>> createBooking({
    required String component,
    required String slotTimeIso,
  }) async {
    try {
      final r = await _dio.post('/bookings', data: {
        'vehicle_id': _vehicleId,
        'service_component': component,
        'slot_time_iso': slotTimeIso,
      });
      return Map<String, dynamic>.from(r.data as Map);
    } catch (e) {
      throw ApiException(_message(e, 'Booking failed. Please try another slot.'));
    }
  }

  Future<void> cancelBooking(String bookingId) async {
    try {
      await _dio.delete('/bookings/$bookingId');
    } catch (e) {
      throw ApiException(_message(e, 'Could not cancel the booking.'));
    }
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

}
