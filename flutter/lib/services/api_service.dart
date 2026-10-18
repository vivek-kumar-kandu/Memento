import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../core/constants/api_constants.dart';
import '../models/assistant_message_model.dart';
import '../models/facility_model.dart';

class ApiService {
  final http.Client _client;

  ApiService({http.Client? client}) : _client = client ?? http.Client();

  /// Search nearby PHCs/CHCs using coordinates and radius.
  /// Calls POST /api/v1/facilities/nearby per backend integration contract.
  Future<NearbySearchResponse> fetchNearbyFacilities({
    required double latitude,
    required double longitude,
    double radiusKm = 30.0,
    int limit = 10,
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

    try {
      final response = await _client
          .post(
            uri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(body),
          )
          .timeout(const Duration(seconds: 8));

      if (response.statusCode == 200) {
        final Map<String, dynamic> data =
            jsonDecode(utf8.decode(response.bodyBytes));
        return NearbySearchResponse.fromJson(data);
      } else if (response.statusCode == 422) {
        throw Exception(
          'Invalid coordinates or parameters: ${response.body}',
        );
      } else {
        throw Exception(
          'Backend returned error (${response.statusCode}): ${response.body}',
        );
      }
    } on SocketException catch (e) {
      throw Exception(
        'Cannot connect to backend at ${ApiConstants.baseUrl}. Please ensure FastAPI backend is running. ($e)',
      );
    } on TimeoutException {
      throw Exception(
        'Backend connection timed out. Please check your network and retry.',
      );
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Unexpected network error: $e');
    }
  }

  /// Send message to the shared assistant endpoint (POST /api/v1/assistant/message).
  /// Reuses existing conversation_id and case_id to prevent duplicate cases.
  Future<AssistantMessageResponse> sendAssistantMessage({
    required String message,
    String channel = 'FLUTTER',
    String? conversationId,
    String? caseId,
    double? latitude,
    double? longitude,
    String? village,
    String? landmark,
    Map<String, dynamic>? context,
  }) async {
    final uri = Uri.parse(ApiConstants.assistantEndpoint);

    Map<String, dynamic>? locationMap;
    if (latitude != null && longitude != null) {
      locationMap = {
        'latitude': latitude,
        'longitude': longitude,
        if (village != null && village.isNotEmpty) 'village': village,
        if (landmark != null && landmark.isNotEmpty) 'landmark': landmark,
      };
    } else if ((village != null && village.isNotEmpty) ||
        (landmark != null && landmark.isNotEmpty)) {
      locationMap = {
        if (village != null && village.isNotEmpty) 'village': village,
        if (landmark != null && landmark.isNotEmpty) 'landmark': landmark,
      };
    }

    final Map<String, dynamic> body = {
      'channel': channel,
      'message': message,
    };
    if (conversationId != null) body['conversation_id'] = conversationId;
    if (caseId != null) body['case_id'] = caseId;
    if (locationMap != null) body['location'] = locationMap;
    if (context != null) body['context'] = context;

    try {
      final response = await _client
          .post(
            uri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(body),
          )
          .timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final Map<String, dynamic> data =
            jsonDecode(utf8.decode(response.bodyBytes));
        return AssistantMessageResponse.fromJson(data);
      } else {
        throw Exception(
          'Assistant API failed (${response.statusCode}): ${response.body}',
        );
      }
    } on SocketException catch (e) {
      throw Exception('Cannot reach backend server: $e');
    } on TimeoutException {
      throw Exception('Assistant request timed out.');
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Unexpected assistant error: $e');
    }
  }

  /// Check backend server status
  Future<bool> checkBackendHealth() async {
    try {
      final uri = Uri.parse(ApiConstants.healthEndpoint);
      final response =
          await _client.get(uri).timeout(const Duration(seconds: 4));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}
