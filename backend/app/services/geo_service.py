import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
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
    Also provides dataset-grounded administrative resolution for districts and subdistricts.
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

        # Administrative hierarchical indices
        self.districts: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.district_names: Dict[str, str] = {}
        self.district_states: Dict[str, str] = {}
        self.district_centroids: Dict[str, Tuple[float, float]] = {}

        self.subdistricts: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
        self.subdistrict_names: Dict[Tuple[str, str], str] = {}
        self.subdistrict_centroids: Dict[Tuple[str, str], Tuple[float, float]] = {}
        self.subdistrict_to_districts: Dict[str, Set[str]] = defaultdict(set)

        # Multi-word aliases and phonetic / spelling normalizations for blocks/tehsils
        self.known_aliases: Dict[str, Tuple[str, str, str]] = {}

    def load_from_file(
        self,
        json_path: Optional[Path] = None,
        clean_csv_path: Optional[Path] = None,
    ) -> None:
        """Load facilities, build BallTree and administrative indexes."""
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

        # Build administrative index maps and centroids
        self._build_administrative_indices()

        self.is_loaded = True
        logger.info(
            f"GeoSpatialIndex ready: {self.valid_count} valid facilities indexed "
            f"({self.quarantined_count} quarantined/missing excluded). "
            f"Indexed {len(self.districts)} districts and {len(self.subdistricts)} subdistricts."
        )

    def _build_administrative_indices(self) -> None:
        """Index facilities by district and subdistrict and calculate centroids."""
        self.districts.clear()
        self.district_names.clear()
        self.district_states.clear()
        self.district_centroids.clear()

        self.subdistricts.clear()
        self.subdistrict_names.clear()
        self.subdistrict_centroids.clear()
        self.subdistrict_to_districts.clear()

        for fac in self.facilities:
            dist = (fac.get("district_name") or "").strip()
            state = (fac.get("state_name") or "").strip()
            subdist = (fac.get("subdistrict_name") or "").strip()

            if not dist:
                continue

            dist_key = dist.lower()
            self.districts[dist_key].append(fac)
            self.district_names[dist_key] = dist
            self.district_states[dist_key] = state

            if subdist:
                subdist_key = subdist.lower()
                self.subdistricts[(dist_key, subdist_key)].append(fac)
                self.subdistrict_names[(dist_key, subdist_key)] = subdist
                self.subdistrict_to_districts[subdist_key].add(dist_key)

        # Compute district centroids
        for dist_key, fac_list in self.districts.items():
            lats = [f["latitude"] for f in fac_list]
            lons = [f["longitude"] for f in fac_list]
            self.district_centroids[dist_key] = (float(np.mean(lats)), float(np.mean(lons)))

        # Compute subdistrict centroids
        for (dist_key, subdist_key), fac_list in self.subdistricts.items():
            lats = [f["latitude"] for f in fac_list]
            lons = [f["longitude"] for f in fac_list]
            self.subdistrict_centroids[(dist_key, subdist_key)] = (
                float(np.mean(lats)),
                float(np.mean(lons)),
            )

        # Canonical multi-word alias dictionary for well-known administrative blocks / localities
        self.known_aliases = {
            "bakshi ka talab": ("lucknow", "b.k.talabe", "Bakshi Ka Talab"),
            "bakshi-ka-talab": ("lucknow", "b.k.talabe", "Bakshi Ka Talab"),
            "b.k. talab": ("lucknow", "b.k.talabe", "Bakshi Ka Talab"),
            "bkt": ("lucknow", "b.k.talabe", "Bakshi Ka Talab"),
            "b.k.talabe": ("lucknow", "b.k.talabe", "Bakshi Ka Talab"),
            "sarojini nagar": ("lucknow", "sarojninagar", "Sarojini Nagar"),
            "sarojninagar": ("lucknow", "sarojninagar", "Sarojini Nagar"),
            "chinhat": ("lucknow", "chinhat", "Chinhat"),
            "mohanlalganj": ("lucknow", "mohanlalganj", "Mohanlalganj"),
            "malihabad": ("lucknow", "malihabad", "Malihabad"),
            "gosaiganj": ("lucknow", "gosaiganj", "Gosaiganj"),
            "gosainganj": ("lucknow", "gosaiganj", "Gosaiganj"),
            "kakori": ("lucknow", "kakori", "Kakori"),
            "mall": ("lucknow", "mall", "Mall"),
            "itaunja": ("lucknow", "b.k.talabe", "Itaunja, Bakshi Ka Talab"),
        }

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

    def resolve_location_text(
        self,
        text: str,
        location_input: Optional[Any] = None,
    ) -> Tuple[Optional[str], Optional[Tuple[float, float]]]:
        """Ground caller location text against the canonical facility dataset.

        Returns:
            (canonical_location_name, (latitude, longitude)) if verified against
            the administrative/facility dataset, otherwise (None, None).
            NEVER fabricates arbitrary coordinates or defaults to (0, 0).
            NEVER performs naive substring matching (e.g. matching 'Tala' in 'talab').
        """
        if not self.is_loaded or not self.facilities:
            return None, None

        candidate_name = None
        if location_input:
            loc_data = (
                location_input.model_dump()
                if hasattr(location_input, "model_dump")
                else location_input
            )
            if isinstance(loc_data, dict):
                candidate_name = (
                    loc_data.get("village")
                    or loc_data.get("landmark")
                    or loc_data.get("name")
                    or loc_data.get("district")
                )

        combined_text = f"{text or ''} {candidate_name or ''}".lower()
        if not combined_text.strip():
            return None, None

        # Clean punctuation for robust whole-word regex matching
        clean_text = re.sub(r"[^\w\s]", " ", combined_text)

        # 1. Step 1: Detect explicit district(s) mentioned in utterance
        detected_districts = []
        for dist_key in self.districts:
            if len(dist_key) >= 3 and re.search(rf"\b{re.escape(dist_key)}\b", clean_text):
                detected_districts.append(dist_key)

        # 2. Step 2: Check multi-word aliases within detected districts FIRST (or overall)
        sorted_aliases = sorted(self.known_aliases.items(), key=lambda x: len(x[0]), reverse=True)
        for alias_phrase, (alias_dist, alias_subdist, display_name) in sorted_aliases:
            if re.search(rf"\b{re.escape(alias_phrase)}\b", clean_text):
                if not detected_districts or alias_dist in detected_districts:
                    centroid = self.subdistrict_centroids.get(
                        (alias_dist, alias_subdist)
                    ) or self.district_centroids.get(alias_dist)
                    if centroid:
                        dist_title = self.district_names.get(alias_dist, alias_dist.title())
                        state_title = self.district_states.get(alias_dist, "")
                        label = f"{display_name}, {dist_title}"
                        if state_title:
                            label += f", {state_title}"
                        return label, centroid

        # 3. Step 3: Check subdistricts belonging to detected district(s)
        if detected_districts:
            for dist_key in detected_districts:
                for (d_key, sd_key), fac_list in self.subdistricts.items():
                    if d_key != dist_key:
                        continue
                    if len(sd_key) < 4:
                        continue
                    sd_pattern = re.sub(r"[^\w\s]", " ", sd_key).strip()
                    if len(sd_pattern) >= 4 and re.search(rf"\b{re.escape(sd_pattern)}\b", clean_text):
                        centroid = self.subdistrict_centroids.get((d_key, sd_key))
                        if centroid:
                            sd_title = self.subdistrict_names.get((d_key, sd_key), sd_key.title())
                            dist_title = self.district_names.get(d_key, d_key.title())
                            state_title = self.district_states.get(d_key, "")
                            label = f"{sd_title}, {dist_title}"
                            if state_title:
                                label += f", {state_title}"
                            return label, centroid

        # 4. Step 4: Check if any subdistrict across India matches uniquely
        if not detected_districts:
            candidate_matches = []
            for (d_key, sd_key), centroid in self.subdistrict_centroids.items():
                if len(sd_key) < 4:
                    continue
                sd_pattern = re.sub(r"[^\w\s]", " ", sd_key).strip()
                if len(sd_pattern) >= 4 and re.search(rf"\b{re.escape(sd_pattern)}\b", clean_text):
                    candidate_matches.append((d_key, sd_key, centroid))

            if len(candidate_matches) == 1:
                d_key, sd_key, centroid = candidate_matches[0]
                sd_title = self.subdistrict_names.get((d_key, sd_key), sd_key.title())
                dist_title = self.district_names.get(d_key, d_key.title())
                state_title = self.district_states.get(d_key, "")
                label = f"{sd_title}, {dist_title}"
                if state_title:
                    label += f", {state_title}"
                return label, centroid
            elif len(candidate_matches) > 1:
                logger.info("Ambiguous subdistrict matches found: %s", candidate_matches)
                return None, None

        # 5. Step 5: Fall back to district centroid if district uniquely specified
        if len(detected_districts) == 1:
            d_key = detected_districts[0]
            centroid = self.district_centroids.get(d_key)
            if centroid:
                dist_title = self.district_names.get(d_key, d_key.title())
                state_title = self.district_states.get(d_key, "")
                label = f"{dist_title}"
                if state_title:
                    label += f", {state_title}"
                return label, centroid

        return None, None

    def get_by_id(self, facility_id: str) -> Optional[Dict[str, Any]]:
        return self.facility_map.get(facility_id)


# Global singleton spatial index
geo_index = GeoSpatialIndex()
