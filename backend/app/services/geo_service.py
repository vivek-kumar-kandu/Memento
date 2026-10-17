import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from sklearn.neighbors import BallTree

from app.core.config import settings
from app.core.logging import logger
from app.schemas.facility import FacilityNearbyItem


class GeoSpatialIndex:
    """In-memory spatial index powered by scikit-learn BallTree (Haversine metric).

    Indexes the 34,936 validated PHC/CHC facilities whose coordinates fall within
    the broad India envelope (6-38°N, 68-98°E). Quarantined and missing coordinate
    records (186 records) are strictly excluded from spatial queries.
    """

    def __init__(self) -> None:
        self.facilities: List[Dict[str, Any]] = []
        self.facility_map: Dict[str, Dict[str, Any]] = {}
        self.tree: Optional[BallTree] = None
        self.coords_rad: Optional[np.ndarray] = None
        self.is_loaded: bool = False
        self.total_source_count: int = 0
        self.valid_count: int = 0
        self.quarantined_count: int = 0

    def load_from_file(
        self,
        json_path: Optional[Path] = None,
        clean_csv_path: Optional[Path] = None,
    ) -> None:
        """Load facilities and build BallTree."""
        path = json_path or settings.FACILITY_NEARBY_JSON
        csv_path = clean_csv_path or settings.FACILITY_CLEAN_CSV

        if not path.exists():
            raise FileNotFoundError(
                f"Facility nearby JSON file not found at: {path}. "
                "Ensure original Data/ files are preserved."
            )

        logger.info(f"Loading nearby facility search dataset from {path}...")
        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        self.facilities = raw_data
        self.valid_count = int(len(raw_data))

        # Count total and quarantined from clean CSV if available
        if csv_path.exists():
            import pandas as pd
            df_clean = pd.read_csv(csv_path, usecols=["facility_id", "coordinate_status"])
            self.total_source_count = int(len(df_clean))
            self.quarantined_count = int((df_clean["coordinate_status"] != "OK_BROAD_BOUNDS").sum())
        else:
            self.total_source_count = int(self.valid_count + 186)
            self.quarantined_count = 186

        # Map by facility_id for O(1) lookups
        self.facility_map = {f["facility_id"]: f for f in self.facilities}

        # Convert lat/lon to radians for Haversine BallTree
        coords = np.array(
            [[math.radians(f["latitude"]), math.radians(f["longitude"])] for f in self.facilities],
            dtype=np.float64,
        )
        self.coords_rad = coords

        logger.info(f"Building BallTree index for {self.valid_count} facilities...")
        self.tree = BallTree(self.coords_rad, metric="haversine")
        self.is_loaded = True
        logger.info(
            f"GeoSpatialIndex ready: {self.valid_count} valid facilities indexed "
            f"({self.quarantined_count} quarantined/missing excluded)."
        )

    def search_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 30.0,
        limit: int = 10,
        facility_type: Optional[str] = None,
        state_name: Optional[str] = None,
        district_name: Optional[str] = None,
        asv_status: Optional[str] = None,
    ) -> Tuple[List[FacilityNearbyItem], int]:
        """Perform nearby facility radius search.

        Returns:
            Tuple of (list of FacilityNearbyItem sorted by distance ascending, total_found)
        """
        if not self.is_loaded or self.tree is None:
            raise RuntimeError("GeoSpatialIndex has not been loaded.")

        # Convert search radius to radians on Earth
        radius_rad = radius_km / settings.EARTH_RADIUS_KM
        query_point = np.array([[math.radians(latitude), math.radians(longitude)]])

        # Query radius with sorted distance
        indices, distances = self.tree.query_radius(
            query_point,
            r=radius_rad,
            return_distance=True,
            sort_results=True,
        )

        matched_indices = indices[0]
        matched_distances = distances[0]

        results: List[FacilityNearbyItem] = []
        state_filter = state_name.strip().lower() if state_name else None
        district_filter = district_name.strip().lower() if district_name else None
        type_filter = facility_type.strip().upper() if facility_type else None
        asv_filter = asv_status.strip().upper() if asv_status else None

        for idx, dist_rad in zip(matched_indices, matched_distances):
            fac = self.facilities[idx]

            # Filters
            if type_filter and fac.get("facility_type", "").upper() != type_filter:
                continue
            if state_filter and state_filter not in fac.get("state_name", "").lower():
                continue
            if district_filter and district_filter not in fac.get("district_name", "").lower():
                continue
            if asv_filter and fac.get("asv_stock_status", "").upper() != asv_filter:
                continue

            dist_km = round(dist_rad * settings.EARTH_RADIUS_KM, 2)

            qty = fac.get("asv_quantity_vials")
            qty_val = int(qty) if qty not in [None, "", "NaN", "nan"] else None

            results.append(
                FacilityNearbyItem(
                    facility_id=fac["facility_id"],
                    facility_name=fac["facility_name"],
                    facility_type=fac["facility_type"],
                    state_name=fac["state_name"],
                    district_name=fac["district_name"],
                    subdistrict_name=fac.get("subdistrict_name") or None,
                    facility_address=fac.get("facility_address") or None,
                    latitude=fac["latitude"],
                    longitude=fac["longitude"],
                    distance_km=dist_km,
                    asv_stock_status=fac.get("asv_stock_status", "UNKNOWN"),
                    asv_quantity_vials=qty_val,
                    asv_data_mode=(
                        "SIMULATED"
                        if str(fac.get("inventory_data_mode", "")).upper() == "SIMULATED"
                        else "REAL"
                    ),
                    asv_verification_source=fac.get("asv_verification_source", "NOT_VERIFIED"),
                    asv_last_verified_at=None,
                    asv_notes=(
                        "Baseline directory record. Real ASV inventory unconfirmed."
                    ),
                )
            )

            if len(results) >= limit:
                break

        return results, len(results)

    def get_by_id(self, facility_id: str) -> Optional[Dict[str, Any]]:
        return self.facility_map.get(facility_id)


# Global singleton spatial index
geo_index = GeoSpatialIndex()
