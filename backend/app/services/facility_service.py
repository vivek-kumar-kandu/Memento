import math
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.db.models.facility import (
    HealthcareFacility,
    ASVInventory,
    CoordinateStatus,
    ASVStockStatus,
    InventoryDataMode,
    VerificationSource,
)
from app.schemas.facility import (
    FacilityNearbyQuery,
    FacilityNearbyResponse,
    FacilityDetailResponse,
    ASVStatusResponse,
    FacilityListResponse,
)
from app.services.geo_service import geo_index


class FacilityService:
    @staticmethod
    async def import_baseline_data_if_empty(session: AsyncSession) -> Dict[str, int]:
        """Check if facilities are loaded into DB. If empty, load all 35,122 rows

        from phc_chc_facilities_clean.csv and initialize their default UNKNOWN ASV records.
        """
        count_res = await session.execute(select(func.count(HealthcareFacility.id)))
        existing_count = count_res.scalar() or 0

        if existing_count > 0:
            logger.info(f"Database already contains {existing_count} facilities. Skipping CSV load.")
            return {"existing_facilities": existing_count}

        csv_path = settings.FACILITY_CLEAN_CSV
        if not csv_path.exists():
            raise FileNotFoundError(f"Source file not found at {csv_path}")

        logger.info(f"Importing clean facilities and default ASV inventory from {csv_path}...")
        df = pd.read_csv(csv_path, low_memory=False)

        facilities_to_add = []
        asv_to_add = []

        total_rows = len(df)
        quarantined_count = 0
        valid_count = 0

        for _, row in df.iterrows():
            fac_id = str(row["facility_id"])
            coord_status = str(row["coordinate_status"])

            lat = None
            lon = None
            if coord_status == CoordinateStatus.OK_BROAD_BOUNDS.value:
                try:
                    lat_val = float(row["latitude"])
                    lon_val = float(row["longitude"])
                    if not (math.isnan(lat_val) or math.isnan(lon_val)):
                        lat = lat_val
                        lon = lon_val
                        valid_count += 1
                    else:
                        coord_status = CoordinateStatus.OUT_OF_BOUNDS_OR_INVALID.value
                        quarantined_count += 1
                except (ValueError, TypeError):
                    coord_status = CoordinateStatus.OUT_OF_BOUNDS_OR_INVALID.value
                    quarantined_count += 1
            else:
                quarantined_count += 1

            subdist = str(row["subdistrict_name"]) if pd.notna(row["subdistrict_name"]) else None
            addr = str(row["facility_address"]) if pd.notna(row["facility_address"]) else None
            val_note = (
                str(row["coordinate_validation_note"])
                if pd.notna(row["coordinate_validation_note"])
                else None
            )

            fac_obj = HealthcareFacility(
                id=fac_id,
                source_row_number=int(row["source_row_number"]) if pd.notna(row["source_row_number"]) else None,
                facility_name=str(row["facility_name"]),
                facility_type=str(row["facility_type"]),
                state_name=str(row["state_name"]),
                district_name=str(row["district_name"]),
                subdistrict_name=subdist,
                facility_address=addr,
                latitude=lat,
                longitude=lon,
                coordinate_status=coord_status,
                coordinate_validation_note=val_note,
                source_active_flag=str(row["source_active_flag"]) if pd.notna(row["source_active_flag"]) else None,
                location_type=str(row["location_type"]) if pd.notna(row["location_type"]) else None,
                source_type_of_facility=str(row["source_type_of_facility"]) if pd.notna(row["source_type_of_facility"]) else None,
                possible_duplicate_name_in_district=str(row["possible_duplicate_name_in_district"]) if pd.notna(row["possible_duplicate_name_in_district"]) else None,
            )
            facilities_to_add.append(fac_obj)

            # ASV Inventory: strictly default to UNKNOWN, quantity null, NOT_VERIFIED
            asv_obj = ASVInventory(
                facility_id=fac_id,
                stock_status=ASVStockStatus.UNKNOWN.value,
                quantity_vials=None,
                data_mode=InventoryDataMode.REAL.value,
                verification_source=VerificationSource.NOT_VERIFIED.value,
                last_inventory_update=None,
                last_verification_timestamp=None,
                notes="Initial baseline import. Real stock unknown.",
            )
            asv_to_add.append(asv_obj)

        # Batch insert for speed
        BATCH_SIZE = 5000
        for i in range(0, len(facilities_to_add), BATCH_SIZE):
            session.add_all(facilities_to_add[i : i + BATCH_SIZE])
            session.add_all(asv_to_add[i : i + BATCH_SIZE])
            await session.flush()

        await session.commit()
        logger.info(
            f"Successfully imported {total_rows} facilities into DB: "
            f"{valid_count} valid coordinates, {quarantined_count} quarantined/missing coordinates."
        )

        return {
            "total_imported": total_rows,
            "valid_coordinates": valid_count,
            "quarantined_coordinates": quarantined_count,
        }

    @staticmethod
    def search_nearby(query: FacilityNearbyQuery) -> FacilityNearbyResponse:
        """Execute nearby spatial radius search using in-memory BallTree index."""
        # Validate coordinates bounds
        if not (-90.0 <= query.latitude <= 90.0 and -180.0 <= query.longitude <= 180.0):
            raise ValueError(
                f"Invalid coordinates: ({query.latitude}, {query.longitude}). "
                "Latitude must be in [-90, 90] and Longitude in [-180, 180]."
            )

        items, total_found = geo_index.search_nearby(
            latitude=query.latitude,
            longitude=query.longitude,
            radius_km=query.radius_km,
            limit=query.limit,
            facility_type=query.facility_type.value if query.facility_type else None,
            state_name=query.state_name,
            district_name=query.district_name,
            asv_status=query.asv_status.value if query.asv_status else None,
        )

        return FacilityNearbyResponse(
            query_latitude=query.latitude,
            query_longitude=query.longitude,
            search_radius_km=query.radius_km,
            total_found=total_found,
            facilities=items,
        )

    @staticmethod
    async def get_facility_by_id(
        facility_id: str, session: AsyncSession
    ) -> Optional[FacilityDetailResponse]:
        """Fetch complete facility record by ID from database."""
        stmt = (
            select(HealthcareFacility)
            .where(HealthcareFacility.id == facility_id)
        )
        res = await session.execute(stmt)
        fac = res.scalar_one_or_none()
        if not fac:
            return None

        asv = fac.asv_inventory
        return FacilityDetailResponse(
            facility_id=fac.id,
            facility_name=fac.facility_name,
            facility_type=fac.facility_type,
            state_name=fac.state_name,
            district_name=fac.district_name,
            subdistrict_name=fac.subdistrict_name,
            facility_address=fac.facility_address,
            latitude=fac.latitude,
            longitude=fac.longitude,
            coordinate_status=fac.coordinate_status,
            coordinate_validation_note=fac.coordinate_validation_note,
            location_type=fac.location_type,
            asv_stock_status=asv.stock_status if asv else ASVStockStatus.UNKNOWN.value,
            asv_quantity_vials=asv.quantity_vials if asv else None,
            asv_data_mode=asv.data_mode if asv else InventoryDataMode.REAL.value,
            asv_verification_source=asv.verification_source if asv else VerificationSource.NOT_VERIFIED.value,
            asv_last_verified_at=asv.last_verification_timestamp if asv else None,
        )

    @staticmethod
    async def get_asv_status(
        facility_id: str, session: AsyncSession
    ) -> Optional[ASVStatusResponse]:
        """Fetch dedicated ASV stock status for a facility."""
        stmt = select(HealthcareFacility).where(HealthcareFacility.id == facility_id)
        res = await session.execute(stmt)
        fac = res.scalar_one_or_none()
        if not fac:
            return None

        asv = fac.asv_inventory
        return ASVStatusResponse(
            facility_id=fac.id,
            facility_name=fac.facility_name,
            facility_type=fac.facility_type,
            state_name=fac.state_name,
            district_name=fac.district_name,
            subdistrict_name=fac.subdistrict_name,
            asv_stock_status=asv.stock_status if asv else ASVStockStatus.UNKNOWN.value,
            asv_quantity_vials=asv.quantity_vials if asv else None,
            data_mode=asv.data_mode if asv else InventoryDataMode.REAL.value,
            verification_source=asv.verification_source if asv else VerificationSource.NOT_VERIFIED.value,
            last_inventory_update=asv.last_inventory_update if asv else None,
            last_verification_timestamp=asv.last_verification_timestamp if asv else None,
        )

    @staticmethod
    async def list_facilities(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        facility_type: Optional[str] = None,
        state_name: Optional[str] = None,
        district_name: Optional[str] = None,
    ) -> FacilityListResponse:
        """List facilities with relational filters."""
        conditions = []
        if facility_type:
            conditions.append(HealthcareFacility.facility_type == facility_type.upper())
        if state_name:
            conditions.append(HealthcareFacility.state_name.ilike(f"%{state_name}%"))
        if district_name:
            conditions.append(HealthcareFacility.district_name.ilike(f"%{district_name}%"))

        count_stmt = select(func.count(HealthcareFacility.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total_res = await session.execute(count_stmt)
        total = total_res.scalar() or 0

        query_stmt = select(HealthcareFacility)
        if conditions:
            query_stmt = query_stmt.where(and_(*conditions))
        query_stmt = query_stmt.offset(skip).limit(limit)

        res = await session.execute(query_stmt)
        facilities = res.scalars().all()

        items = []
        for fac in facilities:
            asv = fac.asv_inventory
            items.append(
                FacilityDetailResponse(
                    facility_id=fac.id,
                    facility_name=fac.facility_name,
                    facility_type=fac.facility_type,
                    state_name=fac.state_name,
                    district_name=fac.district_name,
                    subdistrict_name=fac.subdistrict_name,
                    facility_address=fac.facility_address,
                    latitude=fac.latitude,
                    longitude=fac.longitude,
                    coordinate_status=fac.coordinate_status,
                    coordinate_validation_note=fac.coordinate_validation_note,
                    location_type=fac.location_type,
                    asv_stock_status=asv.stock_status if asv else ASVStockStatus.UNKNOWN.value,
                    asv_quantity_vials=asv.quantity_vials if asv else None,
                    asv_data_mode=asv.data_mode if asv else InventoryDataMode.REAL.value,
                    asv_verification_source=asv.verification_source if asv else VerificationSource.NOT_VERIFIED.value,
                    asv_last_verified_at=asv.last_verification_timestamp if asv else None,
                )
            )

        return FacilityListResponse(
            total=total,
            skip=skip,
            limit=limit,
            facilities=items,
        )


facility_service = FacilityService()
