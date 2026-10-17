from typing import AsyncGenerator
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.logging import logger
from app.db.base import Base
import app.db.models  # Ensures all models are registered on Base.metadata

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def _migrate_schema_sync(sync_conn) -> None:
    """Safely migrate any missing columns or legacy schemas in emergency_cases."""
    inspector = inspect(sync_conn)
    table_names = inspector.get_table_names()
    if "emergency_cases" in table_names:
        existing_cols = {col["name"] for col in inspector.get_columns("emergency_cases")}
        # Check if legacy columns with NOT NULL constraints exist
        if "caller_phone" in existing_cols or "reported_symptoms" in existing_cols:
            logger.info("Migrating legacy emergency_cases schema to new unified schema...")
            sync_conn.execute(text("""
                CREATE TABLE emergency_cases_v2 (
                    id VARCHAR(36) NOT NULL PRIMARY KEY,
                    channel VARCHAR(20) NOT NULL,
                    reporter_name VARCHAR(100),
                    phone_number VARCHAR(20),
                    location JSON,
                    village VARCHAR(100),
                    landmark VARCHAR(200),
                    symptoms JSON,
                    status VARCHAR(20) NOT NULL DEFAULT 'NEW',
                    referral_facility_id VARCHAR(32),
                    referral_status VARCHAR(20),
                    referral_timestamp DATETIME,
                    referral_notes VARCHAR(500),
                    acknowledged_by VARCHAR(100),
                    acknowledged_at DATETIME,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                );
            """))
            sync_conn.execute(text("""
                INSERT INTO emergency_cases_v2 (
                    id, channel, reporter_name, phone_number, village, symptoms, status, referral_facility_id, created_at, updated_at
                )
                SELECT 
                    id, channel, patient_name, caller_phone, location_description, reported_symptoms, status, allocated_facility_id, created_at, updated_at
                FROM emergency_cases;
            """))
            sync_conn.execute(text("DROP TABLE emergency_cases;"))
            sync_conn.execute(text("ALTER TABLE emergency_cases_v2 RENAME TO emergency_cases;"))
            logger.info("Migrated legacy emergency_cases successfully.")
        else:
            needed_cols = [
                ("reporter_name", "VARCHAR(100)"),
                ("phone_number", "VARCHAR(20)"),
                ("location", "JSON"),
                ("village", "VARCHAR(100)"),
                ("landmark", "VARCHAR(200)"),
                ("symptoms", "JSON"),
                ("status", "VARCHAR(20) DEFAULT 'NEW'"),
                ("referral_facility_id", "VARCHAR(32)"),
                ("referral_status", "VARCHAR(20)"),
                ("referral_timestamp", "DATETIME"),
                ("referral_notes", "VARCHAR(500)"),
                ("acknowledged_by", "VARCHAR(100)"),
                ("acknowledged_at", "DATETIME"),
            ]
            for col_name, col_type in needed_cols:
                if col_name not in existing_cols:
                    logger.info(f"Adding missing column {col_name} to emergency_cases")
                    sync_conn.execute(text(f"ALTER TABLE emergency_cases ADD COLUMN {col_name} {col_type}"))



async def init_db() -> None:
    """Initialize database tables and run safe migrations."""
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_migrate_schema_sync)
    logger.info("Database tables initialized successfully.")

