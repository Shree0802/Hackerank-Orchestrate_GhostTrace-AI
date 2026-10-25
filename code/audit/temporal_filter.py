"""Temporal filtering and cutoff enforcement for audit observations."""

from typing import Any, Dict, List, Optional
from code.ingestion.timestamp_utils import is_at_or_before, parse_iso_timestamp

class TemporalFilter:
    """Enforces strict audit_at temporal boundaries on evidence and system observations."""

    @staticmethod
    def filter_observations_by_cutoff(
        observations: List[Dict[str, Any]], audit_at: str
    ) -> List[Dict[str, Any]]:
        """Filter a list of observations to include only those captured at or before audit_at."""
        valid = []
        for obs in observations:
            cap_at = obs.get("captured_at")
            if cap_at and is_at_or_before(cap_at, audit_at):
                valid.append(obs)
        return valid

    @staticmethod
    def get_latest_observation_for_resource(
        observations: List[Dict[str, Any]], audit_at: str
    ) -> Optional[Dict[str, Any]]:
        """Return the latest observation captured at or before audit_at."""
        valid = TemporalFilter.filter_observations_by_cutoff(observations, audit_at)
        if not valid:
            return None
        valid.sort(key=lambda x: parse_iso_timestamp(x["captured_at"]), reverse=True)
        return valid[0]
