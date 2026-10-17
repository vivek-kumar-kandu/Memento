import 'dart:convert';
import 'package:http/http.dart' as http;
import '../core/constants/api_constants.dart';
import '../models/facility_model.dart';

class ApiService {
  final http.Client _client;

  ApiService({http.Client? client}) : _client = client ?? http.Client();

  /// Search nearby PHCs/CHCs using coordinates and radius
  Future<NearbySearchResponse> fetchNearbyFacilities({
    required double latitude,
    required double longitude,
    double radiusKm = 30.0,
    int limit = 15,
    String? facilityType,
  }) async {
    final uri = Uri.parse(ApiConstants.nearbyFacilitiesEndpoint);

    final Map<String, dynamic> body = {
      'latitude': latitude,
      'longitude': longitude,
      'radius_km': radiusKm,
      'limit': limit,
    };

    if (facilityType != null && facilityType.isNotEmpty) {
      body['facility_type'] = facilityType;
    }

    final response = await _client.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );

    if (response.statusCode == 200) {
      final Map<String, dynamic> data = jsonDecode(utf8.decode(response.bodyBytes));
      return NearbySearchResponse.fromJson(data);
    } else {
      throw Exception(
        'Failed to fetch nearby facilities (${response.statusCode}): ${response.body}',
      );
    }
  }

  /// Check backend server status
  Future<bool> checkBackendHealth() async {
    try {
      final uri = Uri.parse(ApiConstants.healthEndpoint);
      final response = await _client.get(uri).timeout(const Duration(seconds: 4));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}
