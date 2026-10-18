class ApiConstants {
  // Use 10.0.2.2 for Android emulator, localhost for web/desktop, or custom LAN IP for physical device
  static const String _defaultUrl = String.fromEnvironment(
    'BACKEND_BASE_URL',
    defaultValue: 'https://sanjeevini-ai.onrender.com',
  );

  static String baseUrl = _defaultUrl;

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
