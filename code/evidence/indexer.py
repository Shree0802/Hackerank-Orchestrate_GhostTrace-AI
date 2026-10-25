"""Indexed evidence store providing temporal and identifier-based retrieval."""

from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import pandas as pd

from code.evidence.json_parser import JSONEvidenceParser
from code.evidence.sql_inspector import SQLEvidenceInspector
from code.evidence.log_parser import LogEvidenceParser
from code.evidence.pdf_parser import PDFEvidenceParser
from code.evidence.image_parser import ImageEvidenceParser
from code.ingestion.timestamp_utils import is_at_or_before

class EvidenceIndexer:
    """Builds and indexes observations across all evidence files."""

    def __init__(self, dataset_dir: Path, df_manifest: pd.DataFrame, df_activity: pd.DataFrame, resolver: Optional[Any] = None):
        self.dataset_dir = Path(dataset_dir)
        self.df_manifest = df_manifest
        self.df_activity = df_activity
        self.resolver = resolver
        
        # In-memory indexes
        self.all_observations: List[Dict[str, Any]] = []
        self.by_resource_id = defaultdict(list)
        self.by_identifier = defaultdict(list)
        self.by_file_id = defaultdict(list)

        self._build_index()

    def _build_index(self):
        for _, row in self.df_manifest.iterrows():
            fid = row["file_id"]
            rel_path = row["file_path"]
            cap_at = row["captured_at"]
            full_path = self.dataset_dir / rel_path

            if not full_path.exists():
                continue

            obs_list = []
            fname = full_path.name.lower()
            if fname.endswith(".json") or fname.endswith(".txt"):
                obs_list = JSONEvidenceParser.parse_file(full_path, fid, cap_at)
            elif fname.endswith(".sql"):
                obs_list = SQLEvidenceInspector.parse_file(full_path, fid, cap_at)
            elif fname.endswith(".log"):
                obs_list = LogEvidenceParser.parse_file(full_path, fid, cap_at)
            elif fname.endswith(".pdf"):
                obs_list = PDFEvidenceParser.parse_file(full_path, fid, cap_at)

            for obs in obs_list:
                self._add_observation(obs)

        # Ingest image console mappings
        image_obs = ImageEvidenceParser.parse_images_from_activity(self.df_activity, self.df_manifest)
        for obs in image_obs:
            self._add_observation(obs)

    def _add_observation(self, obs: Dict[str, Any]):
        self.all_observations.append(obs)
        rid = obs.get("resource_id")
        if rid:
            self.by_resource_id[rid].append(obs)
        fid = obs.get("file_id")
        if fid:
            self.by_file_id[fid].append(obs)
        for ident in obs.get("user_identifiers", []):
            if ident:
                self.by_identifier[ident.lower()].append(obs)

    def get_observations_for_user(
        self, identifiers: Any, audit_at: str
    ) -> List[Dict[str, Any]]:
        """Retrieve all observations associated with any user identifier captured at or before audit_at."""
        if hasattr(identifiers, "all_identifiers"):
            idents = identifiers.all_identifiers()
        elif isinstance(identifiers, str):
            idents = {identifiers}
        else:
            idents = set(identifiers)

        seen = set()
        results = []
        for ident in idents:
            clean = str(ident).strip().lower()
            for obs in self.by_identifier.get(clean, []):
                cap_at = obs["captured_at"]
                if is_at_or_before(cap_at, audit_at):
                    key = (obs["file_id"], obs["resource_id"], obs["status"])
                    if key not in seen:
                        seen.add(key)
                        results.append(obs)
        return results

    def get_observations_for_resource(
        self, resource_id: str, audit_at: str
    ) -> List[Dict[str, Any]]:
        """Retrieve all observations for a specific resource captured at or before audit_at."""
        results = []
        for obs in self.by_resource_id.get(resource_id, []):
            if is_at_or_before(obs["captured_at"], audit_at):
                results.append(obs)
        # Sort by captured_at descending (latest first)
        results.sort(key=lambda x: x["captured_at"], reverse=True)
        return results
