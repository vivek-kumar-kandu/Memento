import logging
from typing import Any, Dict, List, Optional
import httpx

try:
    from config import (
        GRAPH_API_BASE_URL,
        WHATSAPP_ACCESS_TOKEN,
        WHATSAPP_PHONE_NUMBER_ID,
    )
    from models import AssistantMessageResponse, FacilityItem
except ImportError:
    from .config import (
        GRAPH_API_BASE_URL,
        WHATSAPP_ACCESS_TOKEN,
        WHATSAPP_PHONE_NUMBER_ID,
    )
    from .models import AssistantMessageResponse, FacilityItem

logger = logging.getLogger("whatsapp.meta_client")


class MetaWhatsAppClient:
    """Client for dispatching outbound messages via Meta WhatsApp Cloud API."""

    def __init__(
        self,
        phone_number_id: Optional[str] = None,
        access_token: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.phone_number_id = phone_number_id or WHATSAPP_PHONE_NUMBER_ID
        self.access_token = access_token or WHATSAPP_ACCESS_TOKEN
        self.base_url = base_url or GRAPH_API_BASE_URL

    @property
    def is_configured(self) -> bool:
        """Check if real Meta Cloud API credentials are configured."""
        return bool(
            self.phone_number_id
            and self.access_token
            and not self.phone_number_id.startswith("your_")
            and not self.access_token.startswith("your_")
        )

    def format_whatsapp_message(self, response: AssistantMessageResponse) -> str:
        """Formats the backend response into a structured, mobile-friendly WhatsApp message.

        Preserves clinician-approved guidelines, facility details, and ASV disclaimers.
        """
        lines = []

        # 1. Main Actionable Response Text
        if response.response_text:
            lines.append(response.response_text)

        # 2. Case Tracking Information
        if response.case_id:
            lines.append(f"\n📋 *Case Reference:* `{response.case_id}`")
            if response.case_status:
                lines.append(f"• Status: *{response.case_status}*")

        # 3. Nearby Facilities List (when returned by backend)
        if response.nearby_facilities:
            lines.append("\n🏥 *NEARBY HEALTHCARE FACILITIES:*")
            for idx, fac in enumerate(response.nearby_facilities[:3], start=1):
                dist_str = f"{fac.distance_km:.1f} km" if fac.distance_km is not None else "distance unknown"
                lines.append(
                    f"{idx}. *{fac.facility_name}* ({fac.facility_type})\n"
                    f"   📍 Distance: {dist_str} ({fac.district_name}, {fac.state_name})\n"
                    f"   ⚠️ ASV Stock: *{fac.asv_stock_status}* ({fac.asv_verification_source})"
                )

        # 4. Active Referral Notice (if initiated)
        if response.referral:
            ref = response.referral
            status_text = ref.referral_status
            if ref.acknowledged_by:
                status_text += f" (Acknowledged by {ref.acknowledged_by})"
            else:
                status_text += " (Pending hospital confirmation)"
            lines.append(f"\n🚑 *Referral Status:* {status_text}")

        # 5. Safety Warnings & Disclaimers
        safety = response.safety_metadata or {}
        if safety.get("tourniquet_warning"):
            lines.append(f"\n⚠️ *WARNING:* {safety['tourniquet_warning']}")
        if safety.get("asv_safety_notice"):
            lines.append(f"\nℹ️ *ASV Note:* {safety['asv_safety_notice']}")

        # 6. Direct Emergency Helplines
        lines.append("\n📞 *Emergency Helplines:* Call *108* (Ambulance) or *112* (National Emergency) immediately.")

        return "\n".join(lines)

    async def send_text_message(
        self,
        to_phone: str,
        text_body: str,
        client: Optional[httpx.AsyncClient] = None,
    ) -> Dict[str, Any]:
        """Send a plain text message to a WhatsApp user via Meta Cloud API.

        If credentials are not configured (local dev/test), logs safely and returns simulation receipt.
        """
        # Sanitize recipient phone
        recipient = to_phone.strip().replace("+", "")

        if not self.is_configured:
            logger.info(
                "[SIMULATION / DRY-RUN] Outbound WhatsApp to %s: %s",
                recipient,
                text_body[:120] + ("..." if len(text_body) > 120 else ""),
            )
            return {
                "status": "simulated",
                "recipient": recipient,
                "message": text_body,
                "note": "Meta credentials unconfigured. Message simulated successfully.",
            }

        endpoint = f"{self.base_url}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text_body},
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        async def _execute_send(http_client: httpx.AsyncClient) -> httpx.Response:
            return await http_client.post(endpoint, json=payload, headers=headers, timeout=10.0)

        try:
            if client is not None:
                resp = await _execute_send(client)
            else:
                async with httpx.AsyncClient() as default_client:
                    resp = await _execute_send(default_client)

            if resp.status_code in (200, 201):
                data = resp.json()
                logger.info("Outbound WhatsApp message sent to %s (Meta ID: %s)", recipient, data.get("messages", [{}])[0].get("id"))
                return {"status": "sent", "meta_response": data}
            else:
                logger.error(
                    "Meta API error sending to %s (HTTP %s): %s",
                    recipient,
                    resp.status_code,
                    resp.text,
                )
                return {"status": "error", "status_code": resp.status_code, "detail": resp.text}

        except Exception as e:
            logger.error("Exception during Meta API dispatch to %s: %s", recipient, e, exc_info=True)
            return {"status": "failed", "error": str(e)}


# Global singleton Meta client
meta_client = MetaWhatsAppClient()
