class ApiConstants {
  // Use 10.0.2.2 for Android emulator, localhost for web/desktop, or custom LAN IP for physical device
  static const String baseUrl = 'http://localhost:8000';
  
  static const String nearbyFacilitiesEndpoint = '$baseUrl/api/v1/facilities/nearby';
  static const String facilitiesEndpoint = '$baseUrl/api/v1/facilities';
  static const String healthEndpoint = '$baseUrl/health';

  // National Emergency Numbers
  static const String ambulanceNumber = '108';
  static const String emergencyServiceNumber = '112';
}
