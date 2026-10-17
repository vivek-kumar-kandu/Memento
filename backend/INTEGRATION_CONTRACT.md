# DHWANI-SANJEEVANI — BACKEND INTEGRATION CONTRACT & DEVELOPER GUIDE
**Status**: Frozen for Multi-Team Integration (Milestone 2/3 MVP)  
**Target Clients**: Edesy IVR Telephony, WhatsApp Bot, Flutter Mobile App  
**Last Verified Against Live Server**: October 18, 2026 (All 26 Tests Passing)

---

## 1. Quick Start & Server Commands

### Launch the Backend Locally
Run from `D:\Memento\backend` using the project's Python 3.12 environment:
```powershell
# Default binding: 127.0.0.1:8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# To allow Android Emulator / LAN connections from devices on the same Wi-Fi:
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Run Automated Tests
```powershell
python -m pytest
```

### Base URL Reference
- **Localhost (same machine)**: `http://127.0.0.1:8000` or `http://localhost:8000`
- **Android Emulator**: `http://10.0.2.2:8000` (Android routes `10.0.2.2` to host machine)
- **Local Network / Physical Phones**: `http://<YOUR_LAN_IP>:8000` (Requires `--host 0.0.0.0`)
- **Interactive OpenAPI Documentation**: `http://127.0.0.1:8000/docs`
- **JSON Schema**: `http://127.0.0.1:8000/openapi.json`

---

## 2. Channel Connectivity & Enums

### Allowed `channel` Values
All endpoints enforcing a channel expect one of:
- `"IVR"` — Edesy voice telephony integration
- `"WHATSAPP"` — WhatsApp messaging bot
- `"FLUTTER"` — Flutter mobile application

### Allowed `status` (Case Lifecycle) Values
- `"NEW"` — Fresh incident logged; location or symptoms still pending.
- `"TRIAGED"` — Initial symptoms recorded; clinician guidance generated.
- `"REFERRAL_MADE"` — Nearest verified healthcare facility allocated.
- `"RESOLVED"` — Patient transported or admitted.
- `"CLOSED"` — Incident finalized.
- `"CANCELLED"` — Call disconnected or false alarm.

### Allowed `referral_status` Values
- `"PENDING"` — Destination facility identified; transport dispatched or patient en route.
- `"SENT"` — Referral payload transmitted to facility communication system.
- `"ACKNOWLEDGED"` — Authorized facility staff received and confirmed readiness.
- `"REJECTED"` — Facility diverted (e.g. no beds / doctor unavailable).
- `"COMPLETED"` — Patient arrived at facility.

---

## 3. Endpoints & Exact Verified Contracts

### 3.1 Health Check
**`GET /health`** (or `GET /api/v1/health`)
- **Headers**: None required
- **Response** (`200 OK`):
```json
{
  "status": "healthy",
  "timestamp": "2026-10-17T21:53:14.295003+00:00",
  "project": "Dhwani-Sanjeevani Backend",
  "version": "0.1.0",
  "environment": "development",
  "database": {
    "status": "connected",
    "engine": "sqlite+aiosqlite"
  },
  "facility_index": {
    "status": "ready",
    "valid_indexed_facilities": 34936,
    "quarantined_facilities_excluded": 186,
    "total_source_facilities": 35122,
    "asv_baseline_status": "100% UNKNOWN (unverified)"
  }
}
```

---

### 3.2 Shared Conversational Assistant
**`POST /api/v1/assistant/message`**
Primary unified conversational interface for IVR voice prompts, WhatsApp chats, and Flutter text/audio transcription.

#### Request Schema
```json
{
  "channel": "IVR",
  "conversation_id": "optional-uuid-string-or-null",
  "message": "User text, speech-to-text transcript, or button response",
  "case_id": "optional-case-id-e.g-DS-2026-365DF2",
  "location": {
    "latitude": 26.8467,
    "longitude": 80.9462,
    "village": "optional-village-name",
    "landmark": "optional-landmark"
  },
  "context": {}
}
```

#### Turn 1: Caller Reports Snakebite (Location Unknown)
- **Request**:
```json
{
  "channel": "IVR",
  "message": "Bhaiya ko saanp ne kaat liya hai jaldi aao emergency hai"
}
```
- **Response** (`200 OK`):
```json
{
  "conversation_id": "ffb9c6d9-77f2-4612-829c-6c60db6c5ca8",
  "intent": "emergency_report",
  "intent_confidence": 0.6774,
  "case_id": "DS-2026-5A25E7",
  "case_status": "NEW",
  "next_action": "COLLECT_LOCATION",
  "missing_information": ["location"],
  "response_text": "Emergency case recorded (Case ID: DS-2026-5A25E7). Keep the patient completely calm and strictly still. Do not cut or suck the bite wound. If a tourniquet is already tied, DO NOT remove it. Please provide your current village, landmark, or GPS coordinates so we can route you to the nearest hospital.",
  "nearby_facilities": null,
  "referral": null,
  "safety_metadata": {
    "asv_verification_status": "UNKNOWN/NOT_VERIFIED",
    "asv_safety_notice": "Anti-Snake Venom (ASV) availability is NOT GUARANTEED without live confirmation. Do not delay transport to verify stock. Call 108 emergency ambulance immediately.",
    "tourniquet_warning": "Do NOT remove any tourniquet in the field if already applied. Hospital staff will manage tourniquet removal with antivenom prepared.",
    "emergency_numbers": ["108 (Ambulance)", "112 (National Emergency)"]
  }
}
```

#### Turn 2: Caller Provides Location (Reusing `conversation_id`)
- **Request**:
```json
{
  "channel": "IVR",
  "conversation_id": "ffb9c6d9-77f2-4612-829c-6c60db6c5ca8",
  "message": "Hum log Bakshi Ka Talab ke paas khade hain Lucknow me"
}
```
- **Response** (`200 OK`):
```json
{
  "conversation_id": "ffb9c6d9-77f2-4612-829c-6c60db6c5ca8",
  "intent": "location_response",
  "intent_confidence": 0.85,
  "case_id": "DS-2026-5A25E7",
  "case_status": "REFERRAL_MADE",
  "next_action": "DISPATCH_OR_TRANSPORT",
  "missing_information": [],
  "response_text": "Location received. Nearest healthcare facility: Tala (0.0 km away). Referral initiated with status PENDING. Please arrange immediate transport via 108 ambulance. Keep the bitten limb immobilized at heart level.",
  "nearby_facilities": [
    {
      "facility_id": "HCF-018470",
      "facility_name": "Tala",
      "facility_type": "PHC",
      "state_name": "Uttar Pradesh",
      "district_name": "Lucknow",
      "subdistrict_name": "Bakshi Ka Talab",
      "latitude": 27.0543,
      "longitude": 80.9321,
      "distance_km": 0.0,
      "asv_stock_status": "UNKNOWN",
      "asv_quantity_vials": null,
      "asv_data_mode": "REAL",
      "asv_verification_source": "NOT_VERIFIED",
      "asv_last_verified_at": null,
      "asv_notes": "Initial baseline import. Real stock unknown."
    }
  ],
  "referral": {
    "facility_id": "HCF-018470",
    "referral_status": "PENDING",
    "timestamp": "2026-10-17T21:53:14.430553",
    "notes": "Referred to nearest facility Tala (0.0 km away).",
    "acknowledged_by": null,
    "acknowledged_at": null
  },
  "safety_metadata": {
    "asv_verification_status": "UNKNOWN/NOT_VERIFIED",
    "asv_safety_notice": "Anti-Snake Venom (ASV) availability is NOT GUARANTEED without live confirmation. Do not delay transport to verify stock. Call 108 emergency ambulance immediately.",
    "tourniquet_warning": "Do NOT remove any tourniquet in the field if already applied. Hospital staff will manage tourniquet removal with antivenom prepared.",
    "emergency_numbers": ["108 (Ambulance)", "112 (National Emergency)"]
  }
}
```

#### Turn 3: Caller Asks for Human / Operator Escalation
- **Request**:
```json
{
  "channel": "IVR",
  "conversation_id": "ffb9c6d9-77f2-4612-829c-6c60db6c5ca8",
  "message": "Kisi doctor se baat karao turant"
}
```
- **Response** (`200 OK`):
```json
{
  "conversation_id": "ffb9c6d9-77f2-4612-829c-6c60db6c5ca8",
  "intent": "human_help",
  "intent_confidence": 1.0,
  "case_id": "DS-2026-5A25E7",
  "case_status": "REFERRAL_MADE",
  "next_action": "ESCALATE_HUMAN",
  "missing_information": [],
  "response_text": "Connecting you immediately to an emergency 108 medical dispatcher. Please stay on the line. While waiting, keep the patient strictly still and calm."
}
```

---

### 3.3 Emergency Case Management

#### 3.3.1 Create Case
**`POST /api/v1/cases/`**
- **Request**:
```json
{
  "channel": "IVR",
  "reporter_name": "Ramesh Singh",
  "phone_number": "+919876543210",
  "village": "Bakshi Ka Talab",
  "symptoms": ["swelling", "severe_pain"],
  "tourniquet_applied": true
}
```
- **Response** (`201 Created`):
```json
{
  "id": "DS-2026-365DF2",
  "channel": "IVR",
  "status": "TRIAGED",
  "created_at": "2026-10-17T21:53:14.307221",
  "updated_at": "2026-10-17T21:53:14.307221",
  "reporter_name": "Ramesh Singh",
  "phone_number": "+919876543210",
  "location": null,
  "village": "Bakshi Ka Talab",
  "landmark": null,
  "symptoms": ["swelling", "severe_pain"],
  "referral_facility_id": null,
  "referral_status": null,
  "referral_timestamp": null,
  "referral": null,
  "first_aid_advisory": {
    "tourniquet_warning": "CRITICAL MEDICAL ADVISORY: If a tourniquet or tight ligature is already tied, DO NOT REMOVE IT IN THE FIELD. Sudden release can cause rapid systemic distribution of venom and fatal hemodynamic collapse...",
    "do_instructions": [
      "Keep patient completely calm and strictly immobile; movement accelerates venom distribution.",
      "Immobilize the bitten extremity (splint or sling) at or slightly below heart level.",
      "Remove tight items (rings, bangles, watches, tight clothing) before swelling occurs.",
      "Call 108 emergency ambulance immediately and expedite hospital transport."
    ],
    "dont_instructions": [
      "DO NOT cut, slash, or incise the wound.",
      "DO NOT attempt to suck venom by mouth or mechanical pump.",
      "DO NOT apply ice, electricity, herbs, potassium permanganate, or chemicals.",
      "DO NOT attempt to catch or kill the snake; do not delay transport."
    ],
    "safety_note": "Anti-Snake Venom (ASV) is the only definitive treatment for envenomation. Never delay hospital referral to look for local remedies or wait for symptoms to worsen."
  }
}
```

#### 3.3.2 Retrieve Case
**`GET /api/v1/cases/{case_id}`**
- **Response** (`200 OK`): Full case object matching schema above.
- **Response** (`404 Not Found`): `{"detail": "Case 'DS-...' not found"}`

#### 3.3.3 Update Case
**`PATCH /api/v1/cases/{case_id}`**
- **Request**:
```json
{
  "landmark": "Near Kali Mandir",
  "symptoms": ["swelling", "severe_pain", "blurred_vision"],
  "tourniquet_applied": true
}
```
- **Response** (`200 OK`): Returns updated case object.

#### 3.3.4 Create / Attach Referral
**`POST /api/v1/cases/{case_id}/referral`**
- **Request**:
```json
{
  "facility_id": "HCF-031769",
  "referral_status": "PENDING",
  "notes": "Patient in transit via 108 ambulance with severe pain and swelling."
}
```
- **Response** (`200 OK`): Sets case status to `REFERRAL_MADE` and attaches referral info with `acknowledged_by: null`.

#### 3.3.5 Retrieve Referral
**`GET /api/v1/cases/{case_id}/referral`**
- **Response** (`200 OK`):
```json
{
  "facility_id": "HCF-031769",
  "referral_status": "PENDING",
  "timestamp": "2026-10-17T21:53:14.343179",
  "notes": "Patient in transit via 108 ambulance with severe pain and swelling.",
  "acknowledged_by": null,
  "acknowledged_at": null
}
```
- **Response** (`404 Not Found`): If case has no active referral.

#### 3.3.6 Hospital Staff Referral Acknowledgement
**`POST /api/v1/cases/{case_id}/referral/acknowledge`**
- **Request**:
```json
{
  "acknowledged_by": "Dr. S. K. Verma, Incharge CHC",
  "notes": "Emergency bay prepped, resuscitation equipment on standby."
}
```
- **Response** (`200 OK`):
```json
{
  "id": "DS-2026-365DF2",
  "status": "REFERRAL_MADE",
  "referral": {
    "facility_id": "HCF-031769",
    "referral_status": "ACKNOWLEDGED",
    "timestamp": "2026-10-17T21:53:14.343179",
    "notes": "Patient in transit via 108...; Ack note: Emergency bay prepped...",
    "acknowledged_by": "Dr. S. K. Verma, Incharge CHC",
    "acknowledged_at": "2026-10-17T21:53:14.353664"
  }
}
```
- **Response** (`400 Bad Request`): If called on a case without an existing referral.

---

### 3.4 Spatial Facilities & ASV Search (GPS-Enabled)

The backend provides two equivalent methods for finding the nearest validated PHC/CHC facilities using the in-memory BallTree index (34,936 facilities):

#### 3.4.1 GET /api/v1/facilities/nearby (Recommended for Mobile/Flutter Map Views)
- **HTTP Method**: `GET`
- **Path**: `/api/v1/facilities/nearby`
- **Query Parameters**:
  - `latitude` (*required*, `float`, range: `-90.0` to `90.0`): User/device GPS latitude in decimal degrees.
  - `longitude` (*required*, `float`, range: `-180.0` to `180.0`): User/device GPS longitude in decimal degrees.
  - `radius_km` (*optional*, `float`, default: `30.0`, bounds: `> 0.0` to `<= 150.0`): Radial search distance in kilometres.
  - `limit` (*optional*, `int`, default: `10`, bounds: `1` to `50`): Maximum number of facilities to return.
  - `facility_type` (*optional*, `string`): Filter strictly by `"PHC"` or `"CHC"`.
  - `state_name` (*optional*, `string`): Filter by state substring.
  - `district_name` (*optional*, `string`): Filter by district substring.
  - `asv_status` (*optional*, `string`): Filter by `"AVAILABLE"`, `"OUT_OF_STOCK"`, or `"UNKNOWN"`.

- **Example GET Request URL**:
  `GET http://127.0.0.1:8000/api/v1/facilities/nearby?latitude=26.8467&longitude=80.9462&radius_km=30.0&limit=3`

- **Success Response** (`200 OK`):
```json
{
  "query_latitude": 26.8467,
  "query_longitude": 80.9462,
  "search_radius_km": 30.0,
  "total_found": 3,
  "facilities": [
    {
      "facility_id": "HCF-018470",
      "facility_name": "Tala",
      "facility_type": "PHC",
      "state_name": "Uttar Pradesh",
      "district_name": "Lucknow",
      "subdistrict_name": "Bakshi Ka Talab",
      "facility_address": null,
      "latitude": 27.0543,
      "longitude": 80.9321,
      "distance_km": 23.11,
      "asv_stock_status": "UNKNOWN",
      "asv_quantity_vials": null,
      "asv_data_mode": "REAL",
      "asv_verification_source": "NOT_VERIFIED",
      "asv_last_verified_at": null,
      "asv_notes": "Baseline directory record. Real ASV inventory unconfirmed."
    },
    {
      "facility_id": "HCF-018471",
      "facility_name": "Kathwara",
      "facility_type": "PHC",
      "state_name": "Uttar Pradesh",
      "district_name": "Lucknow",
      "subdistrict_name": "Bakshi Ka Talab",
      "facility_address": null,
      "latitude": 27.0182,
      "longitude": 80.8841,
      "distance_km": 20.01,
      "asv_stock_status": "UNKNOWN",
      "asv_quantity_vials": null,
      "asv_data_mode": "REAL",
      "asv_verification_source": "NOT_VERIFIED",
      "asv_last_verified_at": null,
      "asv_notes": "Baseline directory record. Real ASV inventory unconfirmed."
    }
  ],
  "safety_disclaimer": "ASV availability is unverified in baseline facility directories. Always confirm directly or through 108 emergency ambulance dispatch."
}
```

- **Empty Result Response** (When no facilities lie within radius, e.g. open water or remote area):
```json
{
  "query_latitude": 0.0,
  "query_longitude": 0.0,
  "search_radius_km": 10.0,
  "total_found": 0,
  "facilities": [],
  "safety_disclaimer": "ASV availability is unverified in baseline facility directories. Always confirm directly or through 108 emergency ambulance dispatch."
}
```

- **Validation Error Response** (`422 Unprocessable Entity` for out-of-bounds or NaN coordinates):
```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["query", "latitude"],
      "msg": "Input should be less than or equal to 90",
      "input": "105.0"
    }
  ]
}
```

#### 3.4.2 POST /api/v1/facilities/nearby (Equivalent Body-Based Lookup)
- **HTTP Method**: `POST`
- **Path**: `/api/v1/facilities/nearby`
- **Request Body**:
```json
{
  "latitude": 26.8467,
  "longitude": 80.9462,
  "radius_km": 30.0,
  "limit": 10
}
```

---

### 3.5 Flutter Mobile GPS Assistant Integration

The Flutter application must acquire device location permissions (`geolocator` or `location` package on Android/iOS) and pass the structured coordinates directly into the conversational assistant endpoint:

**`POST /api/v1/assistant/message`**

#### 3.5.1 Flutter Discovery Flow (User searches nearby facilities or opens map)
- **Request**:
```json
{
  "channel": "FLUTTER",
  "conversation_id": null,
  "message": "Find nearby healthcare facilities",
  "location": {
    "latitude": 26.8467,
    "longitude": 80.9462,
    "accuracy_m": 15.0
  }
}
```
- **Response** (`200 OK`):
```json
{
  "conversation_id": "4b684cb3-0056-4dc4-b7be-8167664bf87a",
  "intent": "unknown",
  "intent_confidence": 0.19,
  "case_id": null,
  "case_status": null,
  "next_action": "CONFIRM_EMERGENCY",
  "missing_information": [],
  "response_text": "GPS coordinates received (26.8467, 80.9462). Found 5 nearby facilities within 30 km. Nearest: Tala (23.1 km away). If this is a snakebite emergency, please confirm immediately or call 108 ambulance.",
  "nearby_facilities": [
    {
      "facility_id": "HCF-018471",
      "facility_name": "Kathwara",
      "facility_type": "PHC",
      "state_name": "Uttar Pradesh",
      "district_name": "Lucknow",
      "subdistrict_name": "Bakshi Ka Talab",
      "latitude": 27.0182,
      "longitude": 80.8841,
      "distance_km": 20.01,
      "asv_stock_status": "UNKNOWN",
      "asv_quantity_vials": null,
      "asv_data_mode": "REAL",
      "asv_verification_source": "NOT_VERIFIED",
      "asv_last_verified_at": null,
      "asv_notes": "Baseline directory record. Real ASV inventory unconfirmed."
    }
  ],
  "referral": null,
  "safety_metadata": {
    "asv_verification_status": "UNKNOWN/NOT_VERIFIED",
    "asv_safety_notice": "Anti-Snake Venom (ASV) availability is NOT GUARANTEED without live confirmation. Do not delay transport to verify stock. Call 108 emergency ambulance immediately.",
    "tourniquet_warning": "Do NOT remove any tourniquet in the field if already applied. Hospital staff will manage tourniquet removal with antivenom prepared.",
    "emergency_numbers": ["108 (Ambulance)", "112 (National Emergency)"],
    "gps_client_reported_accuracy_m": 15.0,
    "gps_accuracy_notice": "Device GPS accuracy is reported by the client operating system and has not been independently verified."
  }
}
```

*Note: Searching or refreshing location does NOT create an emergency case. `case_id` remains `null` until an emergency is actually reported.*

#### 3.5.2 Flutter Emergency Report with GPS
When a user taps "Report Snakebite" or submits a voice transcript with GPS active:
- **Request**:
```json
{
  "channel": "FLUTTER",
  "conversation_id": "4b684cb3-0056-4dc4-b7be-8167664bf87a",
  "message": "Snake bite emergency, bitten on leg near canal",
  "location": {
    "latitude": 26.8467,
    "longitude": 80.9462,
    "accuracy_m": 8.5
  }
}
```
- **Response** (`200 OK`):
```json
{
  "conversation_id": "4b684cb3-0056-4dc4-b7be-8167664bf87a",
  "intent": "emergency_report",
  "intent_confidence": 0.95,
  "case_id": "DS-2026-9FA120",
  "case_status": "REFERRAL_MADE",
  "next_action": "DISPATCH_OR_TRANSPORT",
  "missing_information": [],
  "response_text": "Emergency case recorded (Case ID: DS-2026-9FA120). Nearest healthcare facility: Kathwara (20.0 km away). Referral initiated with status PENDING. Call 108 ambulance immediately. Keep the patient strictly immobilized. If a tourniquet is tied, do NOT untie it.",
  "nearby_facilities": [ ... ],
  "referral": {
    "facility_id": "HCF-018471",
    "referral_status": "PENDING",
    "timestamp": "2026-10-18T04:36:00.000000",
    "notes": "Auto-referred to nearest facility Kathwara (20.0 km away).",
    "acknowledged_by": null,
    "acknowledged_at": null
  },
  "safety_metadata": { ... }
}
```

#### 3.5.3 Fallback When GPS Permission is Denied or Unavailable
If the user denies GPS permission or device hardware cannot obtain a fix:
1. The Flutter app omits `location` or sends `location: null` or sends only text village/town name: `location: {"village": "Bakshi Ka Talab"}`.
2. The backend falls back gracefully to free-text coordinate regex parsing and facility directory village/subdistrict name resolution.
3. If the location name cannot be resolved, the assistant prompts:
   `"Could not reliably resolve the location name from our facility index. Please provide the nearest major town, block/tehsil name, or GPS coordinates from your phone. Do not delay seeking medical care."`
   `next_action`: `"COLLECT_LOCATION"`, `missing_information`: `["location"]`.
4. Urgent medical advice is NEVER blocked by missing GPS coordinates.

---

## 4. Operational Boundaries: Real vs. Simulated vs. Blocked

| Component | Status | Operational Reality |
|---|---|---|
| **Spatial Facility Search** | **REAL** | In-memory BallTree index querying 34,936 real PHC/CHC facilities in Uttar Pradesh with great-circle Haversine distances. Supports both GET and POST. |
| **Flutter Mobile GPS** | **REAL** | Accepts `location: { latitude, longitude, accuracy_m }`. Validates bounds (-90 to 90, -180 to 180), rejects NaN/Inf. Prioritizes client GPS over free text. |
| **Case & Session Persistence** | **REAL** | Persisted in SQLite `dhwani_sanjeevani.db` (`emergency_cases`, `conversation_sessions`). Reusable across all turns. |
| **Intent Classification** | **REAL** | Scikit-learn TF-IDF character + word n-gram model reloaded from `intent_classifier.joblib`. |
| **Emergency & Human Overrides** | **REAL** | Deterministic keyword checks ensure emergency reports and human help requests are NEVER dropped by low model confidence. |
| **First-Aid Advisories** | **REAL** | Follows WHO and National Guidelines. Strict warning prohibiting field tourniquet removal. |
| **ASV Stock Inventory** | **SIMULATED / UNVERIFIED** | Baseline facilities default strictly to `UNKNOWN` / `NOT_VERIFIED`. Quantity is `null`. No live telephonic stock is faked. |
| **Referral Communication** | **SIMULATED AT BACKEND** | Referral records are tracked in DB. Hospital acknowledgement is distinct and requires an explicit API event. Actual SMS/WhatsApp dispatch to hospital staff depends on sibling messaging clients. |
| **Edesy Telephony Tool Adapter** | **BLOCKED ON CONTRACT** | Telephony HTTP webhook schema and authentication method have not been provided by the IVR team. Generic assistant API is ready. |

---

## 5. Outstanding Edesy Requirements (To Unblock IVR Team)

The generic assistant endpoint `POST /api/v1/assistant/message` is fully functional. To build a direct Edesy native tool adapter, the IVR team must specify:
1. **Tool Invocation Schema**: Does Edesy pass `{"text": "..."}` or `{"user_utterance": "..."}` or a custom JSON envelope?
2. **Output Structure**: Does Edesy expect flat text `{"speech": "..."}` or SSML or structured JSON?
3. **Authentication**: Does Edesy use a header secret (e.g. `X-Edesy-Token`) or HTTP Basic Auth?
4. **Call Lifecycle Events**: Are call-start / call-ended webhooks sent, and what are their payload signatures?

---

## 6. Integration Checklist for Sibling Teams

- [ ] **Flutter Mobile App Team**:
  1. For direct facility map/list discovery, call `GET /api/v1/facilities/nearby?latitude=...&longitude=...&radius_km=30`.
  2. For conversational triage/chat, call `POST /api/v1/assistant/message` with `channel="FLUTTER"`.
  3. Obtain mobile GPS via standard platform permissions (`geolocator`), then include `location: {"latitude": lat, "longitude": lon, "accuracy_m": acc}` in the request payload.
  4. If user denies location permissions, send `location: null` and prompt user for their village/block name.
  5. Store `conversation_id` and `case_id` from response to preserve state across multi-turn messages.
  6. **Local Testing URL**: Android emulator uses `http://10.0.2.2:8000`, iOS simulator uses `http://localhost:8000`, physical device on Wi-Fi uses `http://<HOST_IP>:8000`.

- [ ] **WhatsApp Bot Team**: Use `POST /api/v1/assistant/message` with `channel="WHATSAPP"`. Pass caller's phone number and WhatsApp message text. Store `conversation_id` in chat state to maintain context across turns.

- [ ] **IVR Telephony Team**: Map caller speech transcripts to `POST /api/v1/assistant/message` with `channel="IVR"`. Read back `response_text` to the caller via TTS. If `next_action == "ESCALATE_HUMAN"`, trigger SIP call transfer to 108 emergency queue.
