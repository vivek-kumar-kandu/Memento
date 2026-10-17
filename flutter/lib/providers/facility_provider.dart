import 'package:flutter/foundation.dart';
import 'package:geolocator/geolocator.dart';
import '../models/facility_model.dart';
import '../services/api_service.dart';
import '../services/location_service.dart';

class FacilityProvider with ChangeNotifier {
  final ApiService _apiService = ApiService();
  final LocationService _locationService = LocationService();

  List<FacilityModel> _facilities = [];
  bool _isLoading = false;
  String? _errorMessage;
  double _searchRadiusKm = 30.0;
  String? _selectedFacilityType; // null = all, 'PHC', 'CHC'
  String _safetyDisclaimer =
      'ASV availability is unverified in baseline directories. Confirm via 108 ambulance.';

  double _currentLatitude = LocationService.defaultLat;
  double _currentLongitude = LocationService.defaultLon;
  bool _hasRealLocation = false;

  // Getters
  List<FacilityModel> get facilities => _facilities;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  double get searchRadiusKm => _searchRadiusKm;
  String? get selectedFacilityType => _selectedFacilityType;
  String get safetyDisclaimer => _safetyDisclaimer;
  double get currentLatitude => _currentLatitude;
  double get currentLongitude => _currentLongitude;
  bool get hasRealLocation => _hasRealLocation;

  /// Initialize location and load nearby facilities
  Future<void> initLocationAndSearch() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      Position? position = await _locationService.getCurrentLocation();
      if (position != null) {
        _currentLatitude = position.latitude;
        _currentLongitude = position.longitude;
        _hasRealLocation = true;
      } else {
        _hasRealLocation = false;
      }

      await _executeSearch();
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Change search radius (e.g. 10km, 30km, 50km, 100km)
  Future<void> updateSearchRadius(double radius) async {
    _searchRadiusKm = radius;
    await searchFacilities();
  }

  /// Filter by PHC / CHC / All
  Future<void> updateFacilityType(String? type) async {
    _selectedFacilityType = type;
    await searchFacilities();
  }

  /// Trigger search with current params
  Future<void> searchFacilities() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      await _executeSearch();
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> _executeSearch() async {
    final response = await _apiService.fetchNearbyFacilities(
      latitude: _currentLatitude,
      longitude: _currentLongitude,
      radiusKm: _searchRadiusKm,
      facilityType: _selectedFacilityType,
    );
    _facilities = response.facilities;
    _safetyDisclaimer = response.safetyDisclaimer;
  }
}
