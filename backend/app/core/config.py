from pathlib import Path
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "Dhwani-Sanjeevani Backend"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Server binding
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS: Scoped default origins for local development (Flutter web, local dashboards)
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5000",
    ]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./dhwani_sanjeevani.db"

    # Repository and data paths with multi-environment fallback resolution
    @staticmethod
    def _find_path(relative_data_file: str) -> Path:
        candidates = [
            Path(__file__).resolve().parents[3] / "Data" / relative_data_file,
            Path(__file__).resolve().parents[2] / "Data" / relative_data_file,
            Path.cwd() / "Data" / relative_data_file,
            Path.cwd().parent / "Data" / relative_data_file,
            Path("/opt/render/project/src/Data") / relative_data_file,
        ]
        for c in candidates:
            if c.exists():
                return c
        return candidates[0]

    REPO_ROOT: Path = Path(__file__).resolve().parents[3]
    DATA_DIR: Path = (
        Path(__file__).resolve().parents[3] / "Data"
        if (Path(__file__).resolve().parents[3] / "Data").exists()
        else Path.cwd() / "Data"
    )
    FACILITY_CLEAN_CSV: Path = _find_path.__func__("phc_chc_facilities_clean.csv")
    FACILITY_NEARBY_JSON: Path = _find_path.__func__("phc_chc_facilities_for_nearby_search.json")
    COORDINATE_REVIEW_CSV: Path = _find_path.__func__(
        "Dhwani_Sanjeevani_Facility_Data_Bundle/phc_chc_coordinate_review.csv"
    )

    # Spatial Search Parameters
    DEFAULT_SEARCH_RADIUS_KM: float = 30.0
    MAX_SEARCH_RADIUS_KM: float = 150.0
    DEFAULT_FACILITY_LIMIT: int = 10
    MAX_FACILITY_LIMIT: int = 50
    EARTH_RADIUS_KM: float = 6371.0088

    # India broad geographic bounding envelope for coordinate validation
    INDIA_BOUNDS: dict = {
        "min_lat": 6.0,
        "max_lat": 38.0,
        "min_lon": 68.0,
        "max_lon": 98.0,
    }


settings = Settings()
