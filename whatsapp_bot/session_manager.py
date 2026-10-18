import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Set
from models import UserSession

try:
    from config import SESSION_STORAGE_PATH
except ImportError:
    from .config import SESSION_STORAGE_PATH

logger = logging.getLogger("whatsapp.session_manager")


class SessionManager:
    """Manages persistent session mapping between WhatsApp sender and backend identifiers (conversation_id, case_id).

    Includes message deduplication to prevent re-processing retried Meta webhooks.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or SESSION_STORAGE_PATH)
        self._sessions: Dict[str, UserSession] = {}
        self._processed_message_ids: Set[str] = set()
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Load session state and processed message IDs from JSON file if it exists."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for wa_id, sdata in data.get("sessions", {}).items():
                        self._sessions[wa_id] = UserSession(**sdata)
                    self._processed_message_ids = set(data.get("processed_message_ids", []))
                logger.info(
                    "Loaded %d active sessions and %d processed message IDs from %s",
                    len(self._sessions),
                    len(self._processed_message_ids),
                    self.storage_path,
                )
            except Exception as e:
                logger.error("Failed to load session storage from %s: %s", self.storage_path, e)
                self._sessions = {}
                self._processed_message_ids = set()

    def _save_to_disk(self) -> None:
        """Persist session state and recent processed message IDs to JSON file."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            # Retain up to 2000 recent message IDs to prevent file unbounded growth
            recent_ids = list(self._processed_message_ids)[-2000:]
            payload = {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "sessions": {k: v.model_dump() for k, v in self._sessions.items()},
                "processed_message_ids": recent_ids,
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as e:
            logger.error("Failed to save sessions to disk at %s: %s", self.storage_path, e)

    def is_message_processed(self, message_id: str) -> bool:
        """Checks if a Meta webhook message ID has already been processed."""
        if not message_id:
            return False
        return message_id in self._processed_message_ids

    def record_processed_message(self, message_id: str) -> None:
        """Records an incoming message ID to ensure idempotency."""
        if message_id:
            self._processed_message_ids.add(message_id)
            self._save_to_disk()

    def get_session(self, whatsapp_id: str) -> Optional[UserSession]:
        """Fetch existing session for a WhatsApp sender."""
        return self._sessions.get(whatsapp_id)

    def get_or_create_session(self, whatsapp_id: str) -> UserSession:
        """Retrieve existing session or initialize a fresh session for the sender."""
        if whatsapp_id not in self._sessions:
            self._sessions[whatsapp_id] = UserSession(whatsapp_id=whatsapp_id)
            self._save_to_disk()
            logger.info("Initialized new session for WhatsApp sender: %s", whatsapp_id)
        return self._sessions[whatsapp_id]

    def update_session(
        self,
        whatsapp_id: str,
        conversation_id: Optional[str] = None,
        case_id: Optional[str] = None,
        last_message_id: Optional[str] = None,
        last_user_message: Optional[str] = None,
    ) -> UserSession:
        """Update session state with IDs returned by the backend and save to disk."""
        session = self.get_or_create_session(whatsapp_id)
        if conversation_id:
            session.conversation_id = conversation_id
        if case_id:
            session.case_id = case_id
        if last_message_id:
            session.last_message_id = last_message_id
            self._processed_message_ids.add(last_message_id)
        if last_user_message:
            session.last_user_message = last_user_message

        session.updated_at = datetime.now(timezone.utc).isoformat()
        session.message_count += 1
        self._save_to_disk()
        logger.info(
            "Updated session for %s: conversation_id=%s, case_id=%s, count=%d",
            whatsapp_id,
            session.conversation_id,
            session.case_id,
            session.message_count,
        )
        return session

    def clear_all(self) -> None:
        """Utility for test suites to reset session store."""
        self._sessions.clear()
        self._processed_message_ids.clear()
        if self.storage_path.exists():
            try:
                self.storage_path.unlink()
            except Exception:
                pass


# Global singleton session manager
session_manager = SessionManager()
