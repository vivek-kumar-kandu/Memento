import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;

class ApiConstants {
  // Automatically select host for local development:
  // - Android emulator: http://10.0.2.2:8000
  // - Web / Windows Desktop / iOS Simulator: http://127.0.0.1:8000
  static String get _defaultLocalUrl {
    if (kIsWeb) {
      return 'http://127.0.0.1:8000';
    }
    try {
      if (Platform.isAndroid) {
        return 'http://10.0.2.2:8000';
      }
    } catch (_) {}
    return 'http://127.0.0.1:8000';
  }

  static const String _envUrl = String.fromEnvironment('BACKEND_BASE_URL');

  static String baseUrl = _envUrl.isNotEmpty ? _envUrl : _defaultLocalUrl;

  static String get nearbyFacilitiesEndpoint => '$baseUrl/api/v1/facilities/nearby';
  static String get facilitiesEndpoint => '$baseUrl/api/v1/facilities';
  static String get assistantEndpoint => '$baseUrl/api/v1/assistant/message';
  static String get casesEndpoint => '$baseUrl/api/v1/cases';
  static String get healthEndpoint => '$baseUrl/health';

  // National Emergency Numbers
  static const String ambulanceNumber = '108';
  static const String emergencyServiceNumber = '112';

  /// Helper to configure base URL for emulator, physical device, or production
  static void setBaseUrl(String url) {
    baseUrl = url;
  }
}
