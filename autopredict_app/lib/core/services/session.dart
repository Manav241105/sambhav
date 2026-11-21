import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Signed-in owner session: tokens and the selected vehicle.
///
/// Tokens live in the platform keystore (Keychain / EncryptedSharedPreferences),
/// with an in-memory copy so request interceptors can read them synchronously.
class Session {
  Session._();

  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );
  static const _kAccess = 'ap_access_token';
  static const _kRefresh = 'ap_refresh_token';
  static const _kCustomer = 'ap_customer_id';
  static const _kVehicle = 'ap_vehicle_id';

  static String? accessToken;
  static String? refreshToken;
  static String? customerId;
  static String? vehicleId;

  static bool get isSignedIn => accessToken != null && refreshToken != null;

  /// Load the saved session once at app start.
  static Future<void> load() async {
    try {
      accessToken = await _storage.read(key: _kAccess);
      refreshToken = await _storage.read(key: _kRefresh);
      customerId = await _storage.read(key: _kCustomer);
      vehicleId = await _storage.read(key: _kVehicle);
    } catch (_) {
      // Corrupt or unavailable keystore: start signed out.
      await clear();
    }
  }

  static Future<void> saveTokens(Map<String, dynamic> tokens) async {
    accessToken = tokens['access_token'] as String?;
    refreshToken = tokens['refresh_token'] as String?;
    customerId = (tokens['customer_id'] as String?) ?? customerId;
    await _storage.write(key: _kAccess, value: accessToken);
    await _storage.write(key: _kRefresh, value: refreshToken);
    if (customerId != null) await _storage.write(key: _kCustomer, value: customerId);
  }

  static Future<void> selectVehicle(String? id) async {
    vehicleId = id;
    if (id == null) {
      await _storage.delete(key: _kVehicle);
    } else {
      await _storage.write(key: _kVehicle, value: id);
    }
  }

  static Future<void> clear() async {
    accessToken = refreshToken = customerId = vehicleId = null;
    try {
      await _storage.deleteAll();
    } catch (_) {
      // Nothing more to do; in-memory state is already cleared.
    }
  }
}
