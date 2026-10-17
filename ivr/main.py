import sys
from pathlib import Path
from fastapi import FastAPI
import uvicorn

# Ensure the ivr directory is in sys.path when running main.py directly
_CURRENT_DIR = Path(__file__).resolve().parent
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))

try:
    from config import HOST, PORT, BACKEND_BASE_URL
except ImportError:
    from .config import HOST, PORT, BACKEND_BASE_URL

app = FastAPI(
    title="Sanjeevani IVR Adapter",
    description="Minimal foundation adapter interfacing Edesy IVR with Sanjeevani Backend.",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health-check endpoint to verify adapter status and configuration."""
    return {
        "status": "ok",
        "service": "sanjeevani-ivr-adapter",
        "version": "0.1.0",
        "backend_base_url_configured": bool(BACKEND_BASE_URL),
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
