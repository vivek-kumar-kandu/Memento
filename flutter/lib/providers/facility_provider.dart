import 'package:flutter/foundation.dart';
import '../models/facility_model.dart';
import '../models/assistant_message_model.dart';
import '../services/api_service.dart';
import '../services/location_service.dart';

enum FacilitySearchStatus {
  idle,
  requestingLocation,
  locationFound,
  searchingBackend,
  resultsAvailable,
  noResults,
  locationError,
  backendError,
}

class FacilityProvider with ChangeNotifier {
  final ApiService _apiService;
  final LocationService _locationService;

  FacilityProvider({
    ApiService? apiService,
    LocationService? locationService,
  })  : _apiService = apiService ?? ApiService(),
        _locationService = locationService ?? LocationService();

  FacilitySearchStatus _status = FacilitySearchStatus.idle;
  LocationResult? _lastLocationResult;

  List<FacilityModel> _facilities = [];
  double _searchRadiusKm = 30.0;
  String? _selectedFacilityType; // null = All, 'PHC', 'CHC'
  String _safetyDisclaimer =
      'ASV availability is unverified in baseline facility directories. Always confirm directly or through 108 emergency ambulance dispatch.';

  double _currentLatitude = LocationService.defaultLat;
  double _currentLongitude = LocationService.defaultLon;
  double? _accuracyMeters;
  bool _hasRealLocation = false;

  String? _locationErrorMessage;
  String? _backendErrorMessage;

  // Session persistence for emergency assistant workflow
  String? _conversationId;
  String? _caseId;
  ReferralInfo? _activeReferral;

  // Getters
  FacilitySearchStatus get status => _status;
  bool get isLoading =>
      _status == FacilitySearchStatus.requestingLocation ||
      _status == FacilitySearchStatus.searchingBackend;

  LocationResult? get lastLocationResult => _lastLocationResult;
  List<FacilityModel> get facilities => _facilities;
  double get searchRadiusKm => _searchRadiusKm;
  String? get selectedFacilityType => _selectedFacilityType;
  String get safetyDisclaimer => _safetyDisclaimer;

  double get currentLatitude => _currentLatitude;
  double get currentLongitude => _currentLongitude;
  double? get accuracyMeters => _accuracyMeters;
  bool get hasRealLocation => _hasRealLocation;

  String? get locationErrorMessage => _locationErrorMessage;
  String? get backendErrorMessage => _backendErrorMessage;
  String? get errorMessage => _backendErrorMessage ?? _locationErrorMessage;

  String? get conversationId => _conversationId;
  String? get caseId => _caseId;
  ReferralInfo? get activeReferral => _activeReferral;

  /// Main entry point: Acquires current GPS coordinates, then queries backend.
  /// Prevents duplicate requests if already running.
  Future<void> useCurrentLocationAndSearch() async {
    if (isLoading) return; // Prevent duplicate requests

    _status = FacilitySearchStatus.requestingLocation;
    _locationErrorMessage = null;
    _backendErrorMessage = null;
    notifyListeners();

    final result = await _locationService.getCurrentLocation();
    _lastLocationResult = result;

    if (!result.isSuccess) {
      _status = FacilitySearchStatus.locationError;
      _locationErrorMessage = result.message ?? 'Location could not be acquired.';
      _hasRealLocation = false;
      notifyListeners();
      return;
    }

    // Location found
    _status = FacilitySearchStatus.locationFound;
    _currentLatitude = result.latitude!;
    _currentLongitude = result.longitude!;
    _accuracyMeters = result.accuracy;
    _hasRealLocation = true;
    notifyListeners();

    // Query backend facilities
    await _executeFacilitySearch();
  }

  /// Initial load or refresh helper
  Future<void> initLocationAndSearch() async {
    await useCurrentLocationAndSearch();
  }

  /// Change search radius (15, 30, 50, 100 km) and refresh
  Future<void> updateSearchRadius(double radius) async {
    _searchRadiusKm = radius;
    if (_hasRealLocation) {
      await searchFacilities();
    } else {
      notifyListeners();
    }
  }

  /// Filter by PHC / CHC / All
  Future<void> updateFacilityType(String? type) async {
    _selectedFacilityType = type;
    if (_hasRealLocation) {
      await searchFacilities();
    } else {
      notifyListeners();
    }
  }

  /// Re-run backend search with current coordinates
  Future<void> searchFacilities() async {
    if (isLoading) return;
    await _executeFacilitySearch();
  }

  /// Manual village or landmark emergency lookup fallback
  Future<void> searchByManualLocation(String query) async {
    final trimmed = query.trim();
    if (trimmed.isEmpty || isLoading) return;

    _status = FacilitySearchStatus.searchingBackend;
    _backendErrorMessage = null;
    _locationErrorMessage = null;
    notifyListeners();

    try {
      final response = await _apiService.sendAssistantMessage(
        message: 'Looking for emergency healthcare near $trimmed',
        channel: 'FLUTTER',
        conversationId: _conversationId,
        caseId: _caseId,
        village: trimmed,
      );

      _conversationId = response.conversationId;
      if (response.caseId != null) {
        _caseId = response.caseId;
      }
      if (response.referral != null) {
        _activeReferral = response.referral;
      }

      if (response.nearbyFacilities != null && response.nearbyFacilities!.isNotEmpty) {
        _facilities = response.nearbyFacilities!;
        _status = FacilitySearchStatus.resultsAvailable;
      } else {
        _facilities = [];
        _status = FacilitySearchStatus.noResults;
      }
    } catch (e) {
      _status = FacilitySearchStatus.backendError;
      _backendErrorMessage = e.toString().replaceFirst('Exception: ', '');
    } finally {
      notifyListeners();
    }
  }

  /// Retry the last failed operation
  Future<void> retrySearch() async {
    if (_status == FacilitySearchStatus.locationError || !_hasRealLocation) {
      await useCurrentLocationAndSearch();
    } else {
      await _executeFacilitySearch();
    }
  }

  /// Reset to idle state
  void resetToIdle() {
    _status = FacilitySearchStatus.idle;
    _facilities = [];
    _locationErrorMessage = null;
    _backendErrorMessage = null;
    notifyListeners();
  }

  Future<void> _executeFacilitySearch() async {
    _status = FacilitySearchStatus.searchingBackend;
    _backendErrorMessage = null;
    notifyListeners();

    try {
      final response = await _apiService.fetchNearbyFacilities(
        latitude: _currentLatitude,
        longitude: _currentLongitude,
        radiusKm: _searchRadiusKm,
        facilityType: _selectedFacilityType,
      );

      _facilities = response.facilities;
      _safetyDisclaimer = response.safetyDisclaimer;

      if (_facilities.isEmpty) {
        _status = FacilitySearchStatus.noResults;
      } else {
        _status = FacilitySearchStatus.resultsAvailable;
      }
    } catch (e) {
      _status = FacilitySearchStatus.backendError;
      _backendErrorMessage = e.toString().replaceFirst('Exception: ', '');
    } finally {
      notifyListeners();
    }
  }
}
