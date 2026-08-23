"""Feature engineering pipeline for transaction fraud detection.

Transforms raw transaction dictionaries into ML-ready feature vectors
with velocity, geospatial, temporal, and windowed-aggregation features.
"""

from __future__ import annotations

import logging
import math
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_EARTH_RADIUS_KM = 6_371.0

# Default sliding windows in seconds
_DEFAULT_WINDOWS: List[Tuple[str, int]] = [
    ("1h", 3_600),
    ("24h", 86_400),
    ("7d", 604_800),
]


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two lat/lon points."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# Feature pipeline
# ---------------------------------------------------------------------------


class FeaturePipeline:
    """Extracts ML-ready features from raw transaction records.

    The pipeline maintains lightweight state (last-seen timestamps and
    amounts per entity) to compute velocity and windowed features
    incrementally.

    Parameters
    ----------
    windows : list[tuple[str, int]] | None
        Window definitions as ``(label, seconds)`` pairs.
    geo_lookup : dict[str, tuple[float, float]] | None
        Mapping from country code to ``(lat, lon)`` centroid.
    """

    def __init__(
        self,
        windows: Optional[List[Tuple[str, int]]] = None,
        geo_lookup: Optional[Dict[str, Tuple[float, float]]] = None,
    ) -> None:
        self.windows = windows or _DEFAULT_WINDOWS
        self.geo_lookup = geo_lookup or self._default_geo_lookup()

        # Per-entity history: key -> list of (timestamp, amount)
        self._card_history: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
        self._ip_history: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
        self._device_history: Dict[str, List[Tuple[float, float]]] = defaultdict(list)

        # Last known geolocation per card
        self._last_geo: Dict[str, Tuple[float, float]] = {}

        # Country mismatch state: card -> last country
        self._last_country: Dict[str, str] = {}

        # Feature column order (stable across calls)
        self._feature_names: Optional[List[str]] = None

    @staticmethod
    def _default_geo_lookup() -> Dict[str, Tuple[float, float]]:
        """Return centroids for major countries."""
        return {
            "US": (39.8, -98.6),
            "GB": (55.4, -3.4),
            "DE": (51.2, 10.4),
            "FR": (46.6, 2.2),
            "IN": (20.6, 78.9),
            "BR": (-14.2, -51.9),
            "JP": (36.2, 138.3),
            "CN": (35.9, 104.2),
            "AU": (-25.3, 133.8),
            "CA": (56.1, -106.3),
            "NG": (9.1, 8.7),
            "ZA": (-30.6, 22.9),
            "SG": (1.4, 103.8),
            "AE": (23.4, 53.8),
            "MX": (23.6, -102.6),
        }

    # ------------------------------------------------------------------
    # Velocity features
    # ------------------------------------------------------------------

    def compute_velocity_features(
        self,
        timestamp: float,
        card_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> Dict[str, float]:
        """Compute transaction-count velocity features.

        Returns counts of transactions per card/IP/device within each
        configured time window.
        """
        features: Dict[str, float] = {}

        for label, window_sec in self.windows:
            cutoff = timestamp - window_sec

            if card_id:
                count = sum(
                    1 for ts, _ in self._card_history.get(card_id, []) if ts >= cutoff
                )
                features[f"card_tx_count_{label}"] = float(count)
            else:
                features[f"card_tx_count_{label}"] = 0.0

            if ip_address:
                count = sum(
                    1 for ts, _ in self._ip_history.get(ip_address, []) if ts >= cutoff
                )
                features[f"ip_tx_count_{label}"] = float(count)
            else:
                features[f"ip_tx_count_{label}"] = 0.0

            if device_id:
                count = sum(
                    1
                    for ts, _ in self._device_history.get(device_id, [])
                    if ts >= cutoff
                )
                features[f"device_tx_count_{label}"] = float(count)
            else:
                features[f"device_tx_count_{label}"] = 0.0

        return features

    # ------------------------------------------------------------------
    # Geospatial features
    # ------------------------------------------------------------------

    def compute_geo_features(
        self,
        transaction: Dict[str, Any],
        card_id: Optional[str] = None,
    ) -> Dict[str, float]:
        """Compute geospatial features.

        - Distance from last known transaction location.
        - Binary country mismatch flag.
        """
        features: Dict[str, float] = {}

        lat = transaction.get("latitude")
        lon = transaction.get("longitude")
        country = transaction.get("country_code", "UNKNOWN")

        if card_id and card_id in self._last_geo and lat is not None and lon is not None:
            prev_lat, prev_lon = self._last_geo[card_id]
            features["geo_distance_km"] = _haversine(lat, lon, prev_lat, prev_lon)
        else:
            features["geo_distance_km"] = 0.0

        if card_id and card_id in self._last_country:
            features["geo_country_mismatch"] = float(
                country != self._last_country[card_id]
            )
        else:
            features["geo_country_mismatch"] = 0.0

        # Absolute coordinates (may help tree models)
        features["geo_latitude"] = lat if lat is not None else 0.0
        features["geo_longitude"] = lon if lon is not None else 0.0

        # Distance to country centroid
        centroid = self.geo_lookup.get(country)
        if centroid and lat is not None and lon is not None:
            features["geo_distance_to_centroid"] = _haversine(
                lat, lon, centroid[0], centroid[1]
            )
        else:
            features["geo_distance_to_centroid"] = 0.0

        return features

    # ------------------------------------------------------------------
    # Temporal features
    # ------------------------------------------------------------------

    def compute_temporal_features(
        self,
        timestamp: float,
        card_id: Optional[str] = None,
    ) -> Dict[str, float]:
        """Compute temporal features.

        - Hour of day, day of week, is_weekend.
        - Time since last transaction for the card.
        """
        dt = datetime.utcfromtimestamp(timestamp)
        features: Dict[str, float] = {
            "temporal_hour": float(dt.hour),
            "temporal_day_of_week": float(dt.weekday()),
            "temporal_is_weekend": float(dt.weekday() >= 5),
            "temporal_is_night": float(dt.hour < 6 or dt.hour >= 22),
        }

        if card_id and self._card_history.get(card_id):
            last_ts = self._card_history[card_id][-1][0]
            features["temporal_seconds_since_last"] = timestamp - last_ts
        else:
            features["temporal_seconds_since_last"] = 0.0

        return features

    # ------------------------------------------------------------------
    # Windowed aggregation features
    # ------------------------------------------------------------------

    def _compute_windowed_amount_features(
        self,
        timestamp: float,
        card_id: Optional[str] = None,
    ) -> Dict[str, float]:
        """Mean, std, max, min of transaction amounts per window."""
        features: Dict[str, float] = {}

        history = self._card_history.get(card_id, []) if card_id else []

        for label, window_sec in self.windows:
            cutoff = timestamp - window_sec
            amounts = [amt for ts, amt in history if ts >= cutoff]

            if amounts:
                arr = np.array(amounts, dtype=np.float64)
                features[f"amt_mean_{label}"] = float(arr.mean())
                features[f"amt_std_{label}"] = float(arr.std())
                features[f"amt_max_{label}"] = float(arr.max())
                features[f"amt_min_{label}"] = float(arr.min())
                features[f"amt_count_{label}"] = float(len(arr))
            else:
                for suffix in ("mean", "std", "max", "min", "count"):
                    features[f"amt_{suffix}_{label}"] = 0.0

        return features

    # ------------------------------------------------------------------
    # Main extraction
    # ------------------------------------------------------------------

    def extract_features(
        self,
        transaction: Dict[str, Any],
        *,
        update_state: bool = True,
    ) -> Tuple[np.ndarray, List[str]]:
        """Extract a full feature vector from a raw transaction.

        Parameters
        ----------
        transaction : dict
            Must contain at least ``amount`` and ``timestamp``.
            Recommended keys: ``card_id``, ``ip_address``, ``device_id``,
            ``country_code``, ``latitude``, ``longitude``.
        update_state : bool
            If ``True`` the internal history buffers are updated, which
            is required for correct velocity/windowed features.

        Returns
        -------
        tuple[np.ndarray, list[str]]
            Feature vector and ordered feature names.
        """
        timestamp = float(transaction.get("timestamp", 0.0))
        amount = float(transaction.get("amount", 0.0))
        card_id = transaction.get("card_id")
        ip_address = transaction.get("ip_address")
        device_id = transaction.get("device_id")

        # --- Collect feature blocks ---
        base_features: Dict[str, float] = {
            "amount": amount,
            "amount_log": float(np.log1p(amount)),
        }

        velocity = self.compute_velocity_features(
            timestamp, card_id=card_id, ip_address=ip_address, device_id=device_id
        )
        geo = self.compute_geo_features(transaction, card_id=card_id)
        temporal = self.compute_temporal_features(timestamp, card_id=card_id)
        windowed = self._compute_windowed_amount_features(timestamp, card_id=card_id)

        # Merge all
        all_features = {**base_features, **velocity, **geo, **temporal, **windowed}

        # Stable ordering
        if self._feature_names is None:
            self._feature_names = sorted(all_features.keys())

        vector = np.array(
            [all_features.get(name, 0.0) for name in self._feature_names],
            dtype=np.float64,
        )

        # --- Update state ---
        if update_state:
            if card_id is not None:
                self._card_history[card_id].append((timestamp, amount))
                # Prune old entries (> 30 days)
                cutoff = timestamp - 2_592_000
                self._card_history[card_id] = [
                    (t, a) for t, a in self._card_history[card_id] if t >= cutoff
                ]

                if transaction.get("latitude") is not None and transaction.get("longitude") is not None:
                    self._last_geo[card_id] = (
                        transaction["latitude"],
                        transaction["longitude"],
                    )
                if transaction.get("country_code"):
                    self._last_country[card_id] = transaction["country_code"]

            if ip_address is not None:
                self._ip_history[ip_address].append((timestamp, amount))
                cutoff = timestamp - 2_592_000
                self._ip_history[ip_address] = [
                    (t, a) for t, a in self._ip_history[ip_address] if t >= cutoff
                ]

            if device_id is not None:
                self._device_history[device_id].append((timestamp, amount))
                cutoff = timestamp - 2_592_000
                self._device_history[device_id] = [
                    (t, a) for t, a in self._device_history[device_id] if t >= cutoff
                ]

        return vector, self._feature_names

    def extract_features_batch(
        self,
        transactions: List[Dict[str, Any]],
        *,
        update_state: bool = True,
    ) -> Tuple[np.ndarray, List[str]]:
        """Extract features for a batch of transactions.

        Parameters
        ----------
        transactions : list[dict]
            Ordered list of transactions (oldest first).
        update_state : bool
            Whether to update internal buffers.

        Returns
        -------
        tuple[np.ndarray, list[str]]
            Feature matrix ``(n_samples, n_features)`` and names.
        """
        vectors: List[np.ndarray] = []
        names: Optional[List[str]] = None

        for txn in transactions:
            vec, names = self.extract_features(txn, update_state=update_state)
            vectors.append(vec)

        return np.vstack(vectors), names or []

    def reset(self) -> None:
        """Clear all internal state (e.g. before a new evaluation run)."""
        self._card_history.clear()
        self._ip_history.clear()
        self._device_history.clear()
        self._last_geo.clear()
        self._last_country.clear()
        self._feature_names = None
