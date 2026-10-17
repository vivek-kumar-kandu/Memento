"""Quickstart integration snippet for IVR, WhatsApp, and Flutter developers.

Demonstrates connecting to Dhwani-Sanjeevani backend using standard HTTP POST requests.
"""

import json
import urllib.request

BACKEND_URL = "http://127.0.0.1:8000"


def send_assistant_message(message: str, channel: str = "WHATSAPP", conversation_id: str = None, location: dict = None):
    url = f"{BACKEND_URL}/api/v1/assistant/message"
    payload = {
        "channel": channel,
        "message": message,
        "conversation_id": conversation_id,
        "location": location,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


if __name__ == "__main__":
    print("Testing connection to Dhwani-Sanjeevani Backend...")

    # Step 1: Emergency report
    turn1 = send_assistant_message("Bhai ko saanp ne kaat liya hai emergency hai", channel="WHATSAPP")
    conv_id = turn1["conversation_id"]
    case_id = turn1["case_id"]
    print(f"\n[Turn 1] Case Created: {case_id} | Conversation: {conv_id}")
    print(f"Assistant: {turn1['response_text']}")

    # Step 2: Location response
    turn2 = send_assistant_message("Bakshi Ka Talab ke paas hain", channel="WHATSAPP", conversation_id=conv_id)
    print(f"\n[Turn 2] Case Status: {turn2['case_status']}")
    print(f"Assistant: {turn2['response_text']}")
    if turn2.get("nearby_facilities"):
        print(f"Nearest Facility Allocated: {turn2['nearby_facilities'][0]['facility_name']}")
