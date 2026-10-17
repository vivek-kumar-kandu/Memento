import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from ivr directory if available
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

# Server settings
HOST: str = os.getenv("HOST", "127.0.0.1")
PORT: int = int(os.getenv("PORT", "8001"))

# Sanjeevani Backend API Base URL (provided by FastAPI backend teammate)
BACKEND_BASE_URL: str = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000")
BACKEND_TIMEOUT_SECONDS: float = float(os.getenv("BACKEND_TIMEOUT_SECONDS", "5.0"))
ASSISTANT_ENDPOINT: str = f"{BACKEND_BASE_URL.rstrip('/')}/api/v1/assistant/message"

# Call session settings
DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "en")
MAX_NO_INPUT_RETRIES: int = int(os.getenv("MAX_NO_INPUT_RETRIES", "2"))
MAX_BACKEND_RETRIES: int = int(os.getenv("MAX_BACKEND_RETRIES", "1"))

# Edesy Provider settings (placeholders - do not use real secrets in code)
EDESY_API_KEY: str = os.getenv("EDESY_API_KEY", "")
EDESY_API_SECRET: str = os.getenv("EDESY_API_SECRET", "")
EDESY_WEBHOOK_SECRET: str = os.getenv("EDESY_WEBHOOK_SECRET", "")

