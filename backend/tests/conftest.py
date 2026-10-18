import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.session import init_db, AsyncSessionLocal
from app.services.geo_service import geo_index
from app.services.facility_service import facility_service


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="session", autouse=True)
async def initialize_app_state():
    """Ensure database schema is created, facilities imported, and spatial index loaded."""
    await init_db()
    async with AsyncSessionLocal() as session:
        await facility_service.import_baseline_data_if_empty(session)
    geo_index.load_from_file()
    yield


@pytest_asyncio.fixture(scope="function")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac
