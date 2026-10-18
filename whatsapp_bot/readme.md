# DHWANI-SANJEEVANI — WHATSAPP EMERGENCY BOT ADAPTER

Production-ready Meta WhatsApp Cloud API integration adapter for **Dhwani-Sanjeevani**, a voice-first snakebite emergency assistance and healthcare referral platform.

---

## 1. Architecture & Message Flow

```
[ WhatsApp User ]
       │
       ▼ (HTTPS Webhook)
[ Meta WhatsApp Cloud API ]
       │
       ▼ POST /webhook
[ WhatsApp Bot Adapter (Port 8002) ]
       │  ├── 1. Deduplicate message ID (wamid.XXX)
       │  ├── 2. Retrieve / create session (conversation_id, case_id)
       │  ├── 3. Parse text / GPS location pin
       │  │
       ▼  ▼ POST /api/v1/assistant/message
[ FastAPI Common Backend (Port 8000) ]
       │  ├── Intent classifier (Hinglish/Hindi/English)
       │  ├── Case management (DS-2026-XXXXXX)
       │  └── Spatial facility search (BallTree 34,936 facilities)
       │
       ▼ Returns AssistantMessageResponse
[ WhatsApp Bot Adapter ]
       │  ├── 4. Update session (store conversation_id, case_id)
       │  ├── 5. Format mobile message (facilities, ASV caveats, 108 helpline)
       │  │
       ▼  ▼ POST https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages
[ Meta WhatsApp Cloud API ]
       │
       ▼
[ WhatsApp User Mobile ]
```

---

## 2. Configuration & Environment Variables

Copy `.env.example` to `.env` inside `whatsapp_bot/`:

```bash
cp .env.example .env
```

| Variable | Default Value | Description |
|---|---|---|
| `HOST` | `127.0.0.1` | Binding host for the WhatsApp adapter server |
| `PORT` | `8002` | Port for the WhatsApp adapter server |
| `BACKEND_BASE_URL` | `http://127.0.0.1:8000` | Common FastAPI backend base URL |
| `BACKEND_TIMEOUT_SECONDS`| `10.0` | Timeout for backend assistant calls |
| `MAX_BACKEND_RETRIES` | `1` | Max retry attempts for transient connection errors |
| `WHATSAPP_PHONE_NUMBER_ID` | (Meta Dashboard) | Meta Cloud API Phone Number ID |
| `WHATSAPP_ACCESS_TOKEN` | (Meta Dashboard) | Permanent or temporary System User token |
| `WHATSAPP_VERIFY_TOKEN` | `sanjeevini_webhook_secret_verify_token` | Secret string set in Meta App Webhook settings |
| `GRAPH_API_VERSION` | `v21.0` | Meta Graph API version |
| `SESSION_STORAGE_PATH` | `./whatsapp_sessions.json` | Path to persistent session storage file |

*Note: If `WHATSAPP_ACCESS_TOKEN` is not configured, the bot operates in **Simulation / Dry-Run Mode**, logging outbound responses safely without crashing.*

---

## 3. How to Run the WhatsApp Adapter

```powershell
# From Memento/whatsapp_bot directory:
python main.py
```

Or via Uvicorn directly:
```powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8002 --reload
```

---

## 4. Endpoints Reference

### 4.1 Health Check
**`GET /health`**
- Returns operational status, backend connectivity endpoint, Meta configuration state, and active session counts.

### 4.2 Webhook Verification (Meta Challenge)
**`GET /webhook`**
- Parameters: `hub.mode=subscribe`, `hub.challenge=...`, `hub.verify_token=...`
- Returns plain-text challenge when token matches `WHATSAPP_VERIFY_TOKEN`.

### 4.3 Inbound Message Webhook
**`POST /webhook`**
- Accepts Meta WhatsApp Cloud API message notifications (`entry[].changes[].value.messages[]`).
- Ignores delivery status receipts (`statuses[]`) to avoid creating false cases.
- Deduplicates messages using Meta message ID (`wamid.XXX`).
- Returns `{"status": "ok", "summary": ...}` with HTTP 200 immediately.

### 4.4 Local Developer Simulation Endpoint
**`POST /api/test/simulate-message`**
Allows developers to simulate inbound WhatsApp messages without an active Meta webhook or ngrok tunnel:
```json
{
  "from_phone": "919876543210",
  "message_text": "Mere bhai ko saanp ne kaat liya hai, jaldi madad chahiye."
}
```

---

## 5. Verified 3-Turn Emergency Workflow

### Turn 1 — Emergency Report
- **User:** `"Mere bhai ko saanp ne kaat liya hai, jaldi madad chahiye."`
- **Adapter Action:** Calls backend with `channel="WHATSAPP"`.
- **Backend Response:** Case ID created (e.g. `DS-2026-5A25E7`), `next_action="COLLECT_LOCATION"`.
- **Bot Reply:** Sends emergency first aid guidance (keep still, do not cut/suck) and asks for village or GPS pin. Preserves `conversation_id` and `case_id` in `session_manager`.

### Turn 2 — Location Response
- **User:** `"Hum Lucknow mein Bakshi Ka Talab ke paas hain."` (or sends WhatsApp GPS pin)
- **Adapter Action:** Reuses saved `conversation_id` and `case_id`.
- **Backend Response:** Resolves nearby facilities (e.g. `CHC Mohanlalganj`, 4.2 km).
- **Bot Reply:** Displays facilities with straight-line distance, marks ASV stock strictly as `UNKNOWN / NOT_VERIFIED`, and referral status as `PENDING` (never claiming false hospital acknowledgement).

### Turn 3 — Follow-up Guidance
- **User:** `"Ab kya karna chahiye?"`
- **Adapter Action:** Continues same conversation and case.
- **Bot Reply:** Delivers clinician guidance (limb immobilization, 108 ambulance dispatch, strict prohibition against removing field tourniquets).

---

## 6. Running Automated Tests

Run the full automated test suite (16 tests):
```powershell
python -m pytest tests -v
```

All 16 unit and integration tests verify:
1. `GET /health` returns status 200 and healthy metadata.
2. `GET /webhook` verification succeeds on valid token and rejects invalid tokens with 403.
3. Inbound text messages are extracted and forwarded to backend.
4. Inbound GPS location pins are extracted and forwarded as structured coordinates.
5. Delivery receipts (`statuses[]`) are ignored without creating cases.
6. Webhook retries with identical `wamid` are deduplicated.
7. User sessions persist `conversation_id` and `case_id` to disk across process restarts.
8. Multiple senders maintain isolated sessions.
9. Backend failure produces a truthful emergency fallback without claiming case creation.
10. The complete 3-turn emergency workflow functions seamlessly.

---

## 7. Meta Developer Dashboard Setup (Public Webhook)

To connect this adapter to a live Meta WhatsApp Business number:
1. Launch ngrok to expose port 8002:
   ```bash
   ngrok http 8002
   ```
2. In Meta App Dashboard -> **WhatsApp** -> **Configuration**:
   - **Callback URL:** `https://<YOUR_NGROK_DOMAIN>.ngrok-free.app/webhook`
   - **Verify Token:** `sanjeevini_webhook_secret_verify_token` (matching `WHATSAPP_VERIFY_TOKEN`)
3. Under **Webhook Fields**, subscribe to:
   - `messages`
4. Add your recipient test phone numbers under **API Setup**.