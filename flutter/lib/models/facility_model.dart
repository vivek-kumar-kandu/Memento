class FacilityModel {
  final String facilityId;
  final String facilityName;
  final String facilityType;
  final String stateName;
  final String districtName;
  final String? subdistrictName;
  final double latitude;
  final double longitude;
  final double distanceKm;
  final String asvStockStatus;
  final int? asvQuantityVials;
  final String asvDataMode;
  final String asvVerificationSource;
  final String? asvNotes;

  FacilityModel({
    required this.facilityId,
    required this.facilityName,
    required this.facilityType,
    required this.stateName,
    required this.districtName,
    this.subdistrictName,
    required this.latitude,
    required this.longitude,
    required this.distanceKm,
    required this.asvStockStatus,
    this.asvQuantityVials,
    required this.asvDataMode,
    required this.asvVerificationSource,
    this.asvNotes,
  });

  factory FacilityModel.fromJson(Map<String, dynamic> json) {
    return FacilityModel(
      facilityId: json['facility_id'] ?? '',
      facilityName: json['facility_name'] ?? 'Unknown Health Center',
      facilityType: json['facility_type'] ?? 'PHC',
      stateName: json['state_name'] ?? '',
      districtName: json['district_name'] ?? '',
      subdistrictName: json['subdistrict_name'],
      latitude: (json['latitude'] as num?)?.toDouble() ?? 0.0,
      longitude: (json['longitude'] as num?)?.toDouble() ?? 0.0,
      distanceKm: (json['distance_km'] as num?)?.toDouble() ?? 0.0,
      asvStockStatus: json['asv_stock_status'] ?? 'UNKNOWN',
      asvQuantityVials: json['asv_quantity_vials'],
      asvDataMode: json['asv_data_mode'] ?? 'REAL',
      asvVerificationSource: json['asv_verification_source'] ?? 'NOT_VERIFIED',
      asvNotes: json['asv_notes'],
    );
  }
}

class NearbySearchResponse {
  final double queryLatitude;
  final double queryLongitude;
  final double searchRadiusKm;
  final int totalFound;
  final List<FacilityModel> facilities;
  final String safetyDisclaimer;

  NearbySearchResponse({
    required this.queryLatitude,
    required this.queryLongitude,
    required this.searchRadiusKm,
    required this.totalFound,
    required this.facilities,
    required this.safetyDisclaimer,
  });

  factory NearbySearchResponse.fromJson(Map<String, dynamic> json) {
    var rawList = json['facilities'] as List? ?? [];
    List<FacilityModel> items =
        rawList.map((item) => FacilityModel.fromJson(item)).toList();

    return NearbySearchResponse(
      queryLatitude: (json['query_latitude'] as num?)?.toDouble() ?? 0.0,
      queryLongitude: (json['query_longitude'] as num?)?.toDouble() ?? 0.0,
      searchRadiusKm: (json['search_radius_km'] as num?)?.toDouble() ?? 30.0,
      totalFound: json['total_found'] ?? 0,
      facilities: items,
      safetyDisclaimer: json['safety_disclaimer'] ??
          'ASV availability is unverified. Always confirm through 108 emergency dispatch.',
    );
  }
}
