import 'facility_model.dart';

class ReferralInfo {
  final String facilityId;
  final String referralStatus;
  final String? timestamp;
  final String? notes;
  final String? acknowledgedBy;
  final String? acknowledgedAt;

  ReferralInfo({
    required this.facilityId,
    required this.referralStatus,
    this.timestamp,
    this.notes,
    this.acknowledgedBy,
    this.acknowledgedAt,
  });

  factory ReferralInfo.fromJson(Map<String, dynamic> json) {
    return ReferralInfo(
      facilityId: json['facility_id'] ?? '',
      referralStatus: json['referral_status'] ?? 'PENDING',
      timestamp: json['timestamp'],
      notes: json['notes'],
      acknowledgedBy: json['acknowledged_by'],
      acknowledgedAt: json['acknowledged_at'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'facility_id': facilityId,
      'referral_status': referralStatus,
      'timestamp': timestamp,
      'notes': notes,
      'acknowledged_by': acknowledgedBy,
      'acknowledged_at': acknowledgedAt,
    };
  }
}

class AssistantMessageResponse {
  final String conversationId;
  final String intent;
  final double intentConfidence;
  final String responseText;
  final String? caseId;
  final String? caseStatus;
  final String nextAction;
  final List<String> missingInformation;
  final List<FacilityModel>? nearbyFacilities;
  final ReferralInfo? referral;
  final Map<String, dynamic> safetyMetadata;

  AssistantMessageResponse({
    required this.conversationId,
    required this.intent,
    required this.intentConfidence,
    required this.responseText,
    this.caseId,
    this.caseStatus,
    required this.nextAction,
    this.missingInformation = const [],
    this.nearbyFacilities,
    this.referral,
    this.safetyMetadata = const {},
  });

  factory AssistantMessageResponse.fromJson(Map<String, dynamic> json) {
    List<FacilityModel>? facilities;
    if (json['nearby_facilities'] != null && json['nearby_facilities'] is List) {
      facilities = (json['nearby_facilities'] as List)
          .map((item) => FacilityModel.fromJson(item as Map<String, dynamic>))
          .toList();
    }

    ReferralInfo? ref;
    if (json['referral'] != null && json['referral'] is Map<String, dynamic>) {
      ref = ReferralInfo.fromJson(json['referral']);
    }

    List<String> missing = [];
    if (json['missing_information'] != null && json['missing_information'] is List) {
      missing = List<String>.from(json['missing_information']);
    }

    return AssistantMessageResponse(
      conversationId: json['conversation_id'] ?? '',
      intent: json['intent'] ?? 'unknown',
      intentConfidence: (json['intent_confidence'] as num?)?.toDouble() ?? 0.0,
      responseText: json['response_text'] ?? '',
      caseId: json['case_id'],
      caseStatus: json['case_status'],
      nextAction: json['next_action'] ?? 'NONE',
      missingInformation: missing,
      nearbyFacilities: facilities,
      referral: ref,
      safetyMetadata: json['safety_metadata'] is Map<String, dynamic>
          ? json['safety_metadata']
          : {},
    );
  }
}
