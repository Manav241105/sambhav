import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';

final _api = ApiService();

// ── Bookings list ───────────────────────────────────────────────────────────
class BookingNotifier extends StateNotifier<AsyncValue<List<Map<String, dynamic>>>> {
  BookingNotifier() : super(const AsyncValue.loading()) {
    _load();
  }

  Future<void> _load() async {
    state = const AsyncValue.loading();
    try {
      final bookings = await _api.getBookings();
      state = AsyncValue.data(bookings);
    } catch (e, s) {
      state = AsyncValue.error(e, s);
    }
  }

  Future<Map<String, dynamic>> createBooking(Map<String, dynamic> body) async {
    final result = await _api.createBooking(body);
    await _load();
    return result;
  }

  Future<void> cancelBooking(String id) async {
    await _api.cancelBooking(id);
    await _load();
  }

  Future<void> rescheduleBooking(String id, Map<String, dynamic> updates) async {
    await _api.patchBooking(id, updates);
    await _load();
  }

  Future<void> refresh() => _load();
}

final bookingProvider = StateNotifierProvider<BookingNotifier, AsyncValue<List<Map<String, dynamic>>>>(
  (_) => BookingNotifier(),
);

// ── Available slots ──────────────────────────────────────────────────────────
final availableSlotsProvider = FutureProvider.family<List<Map<String, dynamic>>, String>(
  (ref, date) => _api.getAvailableSlots(date),
);
