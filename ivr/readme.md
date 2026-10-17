using edesy for call recording and speech to text and text to speech

# Dhwani-Sanjeevani — IVR Adapter Component

The IVR adapter interfaces telephony and conversational voice providers (Edesy) with the Dhwani-Sanjeevani FastAPI backend service.

---

## 1. Call-Flow Architecture

```
[ Caller ] <==== Telephony ====> [ Edesy Platform (ASR / TTS) ]
                                          |
                +-------------------------+-------------------------+
                | (1) Asynchronous Events | (2) Synchronous Tool    |
                v                         v                         v
     POST /api/v1/edesy/webhook  POST /api/v1/edesy/tool  POST /api/v1/ivr/call/*
                |                         |                         |
                +-------------------------+-------------------------+
                                          |
                                          v
                              [ ConversationController ]
                                          |
                                          v
                                [ BackendClient ]
                                          |
                          POST /api/v1/assistant/message
                                          |
                                          v
                         [ Dhwani-Sanjeevani Backend ]
```

### Call Flow Sequence
1. **Inbound Call Initiation:** Caller dials the emergency helpline. Edesy posts `call.initiated` or invokes the initial greeting prompt.
2. **Greeting:** Adapter returns natural greeting instructing caller to describe the emergency and state their location.
3. **Turn 1 (Symptom/Incident Report):** Caller describes the snakebite. Transcript is sent to `POST /api/v1/assistant/message`. Backend registers the case, creates `conversation_id` and `case_id`, and returns `next_action="COLLECT_LOCATION"`.
4. **Turn 2 (Location Collection):** Caller provides landmark/village. Adapter sends transcript with the same `conversation_id`. Backend resolves nearby facilities with ASV inventory status.
5. **ASV & Referral Guidance:** Spoken response communicates nearest facility details. ASV availability is explicitly treated as **unverified** unless verified through authorized operational reports.
6. **Error / Escalation:** Network timeouts or operator requests safely escalate to human dispatch (108) with clinical first-aid instructions (stay calm, still, no tourniquets, no incisions).

---

## 2. Backend Integration Contract

- **Endpoint:** `POST {BACKEND_BASE_URL}/api/v1/assistant/message`
- **Default Local Development URL:** `http://127.0.0.1:8000`

### Request Payload
```json
{
  "message": "A snake bit my brother on his foot in the field",
  "channel": "IVR",
  "conversation_id": "optional-uuid-on-subsequent-turns",
  "case_id": "optional-case-id-on-subsequent-turns",
  "caller_phone": "+919876543210",
  "language": "en"
}
```

### Response Payload
```json
{
  "response_text": "Keep the patient calm and still. Where are you located?",
  "next_action": "COLLECT_LOCATION",
  "conversation_id": "conv-uuid-12345",
  "case_id": "case-9988",
  "case_status": "CREATED",
  "facilities": [
    {
      "facility_id": "FAC-001",
      "facility_name": "Rampur CHC",
      "distance_km": 12.4,
      "asv_stock_status": "UNKNOWN"
    }
  ],
  "safety_disclaimer": "ASV stock is unverified; confirm via 108 ambulance dispatch."
}
```

---

## 3. Environment Configuration

Copy `ivr/.env.example` to `ivr/.env`:

```bash
# Server Settings
HOST=127.0.0.1
PORT=8001

# Backend Connection
BACKEND_BASE_URL=http://127.0.0.1:8000
BACKEND_TIMEOUT_SECONDS=5.0

# Call Session Parameters
DEFAULT_LANGUAGE=en
MAX_NO_INPUT_RETRIES=2
MAX_BACKEND_RETRIES=1

# Edesy Provider Placeholders
EDESY_API_KEY=your_edesy_api_key_here
EDESY_API_SECRET=your_edesy_api_secret_here
EDESY_WEBHOOK_SECRET=your_edesy_webhook_secret_here
```

---

## 4. How to Run Locally

### Start the IVR Adapter Server
From within the `ivr/` folder:
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```
Or simply:
```bash
python main.py
```

### Check Server Health
```bash
curl http://127.0.0.1:8001/health
```

---

## 5. How to Run Automated Tests

From within the `ivr/` folder:
```bash
python -m pytest tests/ -v
```

---

## 6. Telephony Integration (Edesy)

- **Webhook Route (Async Lifecycle):** `POST /api/v1/edesy/webhook`
- **Tool Route (Sync Conversational AI):** `POST /api/v1/edesy/tool`
- **Live Deployment Requirement:** An external Edesy voice bot requires a publicly accessible HTTPS endpoint (e.g. reverse proxy, cloud deployment, or HTTPS tunnel). Local loopback addresses (`127.0.0.1`) cannot be called directly by external telephony clouds.