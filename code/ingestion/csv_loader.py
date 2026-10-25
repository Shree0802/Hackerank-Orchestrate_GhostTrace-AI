"""Robust loaders and schema validators for all supplied challenge CSV files."""

import os
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

class CSVDataLoader:
    """Loads and validates participant CSV datasets."""

    def __init__(self, dataset_dir: Path):
        self.dataset_dir = Path(dataset_dir)
        if not self.dataset_dir.exists():
            raise FileNotFoundError(f"Dataset directory not found: {self.dataset_dir}")

    def load_deletion_requests(self, filename: str = "deletion_requests.csv") -> pd.DataFrame:
        path = self.dataset_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Requests file not found: {path}")
        df = pd.read_csv(path, dtype=str)
        required = ["case_id", "email", "requested_at", "reported_status", "reported_at", "audit_at", "request_text"]
        self._validate_columns(df, required, filename)
        # Normalize whitespace in identifiers
        df["case_id"] = df["case_id"].str.strip()
        df["email"] = df["email"].str.strip()
        df["reported_status"] = df["reported_status"].str.strip()
        return df

    def load_sample_deletion_requests(self) -> pd.DataFrame:
        return self.load_deletion_requests("sample_deletion_requests.csv")

    def load_user_identities(self) -> pd.DataFrame:
        path = self.dataset_dir / "user_identities.csv"
        if not path.exists():
            raise FileNotFoundError(f"Identities file not found: {path}")
        df = pd.read_csv(path, dtype=str)
        required = ["user_id", "name", "email", "phone", "email_hash", "updated_at"]
        self._validate_columns(df, required, "user_identities.csv")
        df["user_id"] = df["user_id"].str.strip()
        df["email"] = df["email"].str.strip()
        return df

    def load_user_audit_log(self) -> pd.DataFrame:
        path = self.dataset_dir / "user_audit_log.csv"
        if not path.exists():
            raise FileNotFoundError(f"Audit log file not found: {path}")
        df = pd.read_csv(path, dtype=str)
        required = ["audit_id", "user_id", "event_time", "field_name", "old_value", "new_value"]
        self._validate_columns(df, required, "user_audit_log.csv")
        df["user_id"] = df["user_id"].str.strip()
        df["field_name"] = df["field_name"].str.strip()
        return df

    def load_system_activity(self) -> pd.DataFrame:
        path = self.dataset_dir / "system_activity.csv"
        if not path.exists():
            raise FileNotFoundError(f"System activity file not found: {path}")
        df = pd.read_csv(path, dtype=str)
        required = ["activity_id", "event_time", "event_type", "source_system", "target_system", "resource_id", "reported_result", "details"]
        self._validate_columns(df, required, "system_activity.csv")
        df["activity_id"] = df["activity_id"].str.strip()
        df["resource_id"] = df["resource_id"].str.strip()
        df["event_type"] = df["event_type"].str.strip()
        return df

    def load_deletion_rules(self) -> pd.DataFrame:
        path = self.dataset_dir / "deletion_rules.csv"
        if not path.exists():
            raise FileNotFoundError(f"Deletion rules file not found: {path}")
        df = pd.read_csv(path, dtype=str)
        required = ["rule_id", "data_category", "condition", "required_action"]
        self._validate_columns(df, required, "deletion_rules.csv")
        df["data_category"] = df["data_category"].str.strip()
        df["required_action"] = df["required_action"].str.strip()
        return df

    def load_evidence_manifest(self) -> pd.DataFrame:
        path = self.dataset_dir / "evidence_files.csv"
        if not path.exists():
            raise FileNotFoundError(f"Evidence manifest file not found: {path}")
        df = pd.read_csv(path, dtype=str)
        required = ["file_id", "file_path", "origin", "captured_at"]
        self._validate_columns(df, required, "evidence_files.csv")
        df["file_id"] = df["file_id"].str.strip()
        df["file_path"] = df["file_path"].str.strip()
        return df

    def _validate_columns(self, df: pd.DataFrame, required: List[str], filename: str):
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns {missing} in {filename}")
