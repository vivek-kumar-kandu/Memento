import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env file from whatsapp_bot directory if available
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

# Server settings
HOST: str = os.getenv("HOST", "127.0.0.1")
PORT: int = int(os.getenv("PORT", "8002"))

# Backend configuration
BACKEND_BASE_URL: str = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
ASSISTANT_ENDPOINT: str = f"{BACKEND_BASE_URL}/api/v1/assistant/message"
BACKEND_TIMEOUT_SECONDS: float = float(os.getenv("BACKEND_TIMEOUT_SECONDS", "10.0"))
MAX_BACKEND_RETRIES: int = int(os.getenv("MAX_BACKEND_RETRIES", "1"))

# Meta WhatsApp Cloud API credentials
WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_ACCESS_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "sanjeevini_webhook_secret_verify_token")
GRAPH_API_VERSION: str = os.getenv("GRAPH_API_VERSION", "v21.0")
GRAPH_API_BASE_URL: str = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
WHATSAPP_APP_SECRET: Optional[str] = os.getenv("WHATSAPP_APP_SECRET", None)

# Session persistence
_DEFAULT_SESSION_FILE = Path(__file__).resolve().parent / "whatsapp_sessions.json"
SESSION_STORAGE_PATH: str = os.getenv("SESSION_STORAGE_PATH", str(_DEFAULT_SESSION_FILE))

# Logging settings
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
