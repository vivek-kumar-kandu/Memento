import 'dart:async';
import 'package:geolocator/geolocator.dart';

enum LocationStatus {
  success,
  serviceDisabled,
  permissionDenied,
  permissionDeniedForever,
  timeout,
  error,
}

class LocationResult {
  final LocationStatus status;
  final double? latitude;
  final double? longitude;
  final double? accuracy;
  final String? message;

  const LocationResult({
    required this.status,
    this.latitude,
    this.longitude,
    this.accuracy,
    this.message,
  });

  bool get isSuccess =>
      status == LocationStatus.success &&
      latitude != null &&
      longitude != null;

  factory LocationResult.success({
    required double latitude,
    required double longitude,
    double? accuracy,
  }) {
    return LocationResult(
      status: LocationStatus.success,
      latitude: latitude,
      longitude: longitude,
      accuracy: accuracy,
    );
  }

  factory LocationResult.failure(LocationStatus status, String message) {
    return LocationResult(status: status, message: message);
  }
}

class LocationService {
  // Default fallback reference coordinates (e.g. Central India / New Delhi)
  static const double defaultLat = 28.6139;
  static const double defaultLon = 77.2090;

  // Pluggable delegates for testability and mocking
  final Future<bool> Function()? serviceEnabledChecker;
  final Future<LocationPermission> Function()? permissionChecker;
  final Future<LocationPermission> Function()? permissionRequester;
  final Future<Position> Function({LocationSettings? locationSettings})?
      positionRetriever;

  LocationService({
    this.serviceEnabledChecker,
    this.permissionChecker,
    this.permissionRequester,
    this.positionRetriever,
  });

  /// Requests permission only when called, captures coordinates & accuracy,
  /// handles timeouts, disabled services, and permission states cleanly.
  Future<LocationResult> getCurrentLocation({
    Duration timeout = const Duration(seconds: 10),
  }) async {
    try {
      // 1. Verify if location services are enabled on device
      final bool serviceEnabled = serviceEnabledChecker != null
          ? await serviceEnabledChecker!()
          : await Geolocator.isLocationServiceEnabled();

      if (!serviceEnabled) {
        return LocationResult.failure(
          LocationStatus.serviceDisabled,
          'Location services are disabled on your device. Please enable GPS in settings or enter your village/landmark manually.',
        );
      }

      // 2. Check current permission status
      LocationPermission permission = permissionChecker != null
          ? await permissionChecker!()
          : await Geolocator.checkPermission();

      if (permission == LocationPermission.denied) {
        permission = permissionRequester != null
            ? await permissionRequester!()
            : await Geolocator.requestPermission();

        if (permission == LocationPermission.denied) {
          return LocationResult.failure(
            LocationStatus.permissionDenied,
            'Location permission was denied. You can search manually by village/landmark or retry.',
          );
        }
      }

      if (permission == LocationPermission.deniedForever) {
        return LocationResult.failure(
          LocationStatus.permissionDeniedForever,
          'Location permissions are permanently denied. Please enable them in app settings or use manual location search.',
        );
      }

      // 3. Acquire current location fix with accuracy and timeout
      final Position position = positionRetriever != null
          ? await positionRetriever!(
              locationSettings: LocationSettings(
                accuracy: LocationAccuracy.high,
                timeLimit: timeout,
              ),
            )
          : await Geolocator.getCurrentPosition(
              locationSettings: LocationSettings(
                accuracy: LocationAccuracy.high,
                timeLimit: timeout,
              ),
            );

      return LocationResult.success(
        latitude: position.latitude,
        longitude: position.longitude,
        accuracy: position.accuracy,
      );
    } on TimeoutException {
      return LocationResult.failure(
        LocationStatus.timeout,
        'GPS location request timed out. Please retry or enter your village/landmark manually.',
      );
    } catch (e) {
      return LocationResult.failure(
        LocationStatus.error,
        'Unable to acquire device location: ${e.toString()}',
      );
    }
  }

  /// Backward-compatible method returning Position or null
  Future<Position?> getCurrentPosition() async {
    final result = await getCurrentLocation();
    if (result.isSuccess) {
      return Position(
        latitude: result.latitude!,
        longitude: result.longitude!,
        timestamp: DateTime.now(),
        accuracy: result.accuracy ?? 0.0,
        altitude: 0.0,
        altitudeAccuracy: 0.0,
        heading: 0.0,
        headingAccuracy: 0.0,
        speed: 0.0,
        speedAccuracy: 0.0,
      );
    }
    return null;
  }
}
