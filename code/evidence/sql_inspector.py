"""SQLite inspector and parser for SQL snapshot database dumps."""

import re
import sqlite3
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

class SQLEvidenceInspector:
    """Inspects SQL snapshot dumps using SQLite-compatible execution and queries."""

    @staticmethod
    def parse_file(file_path: Path, file_id: str, captured_at: str) -> List[Dict[str, Any]]:
        observations = []
        with open(file_path, "r", encoding="utf-8") as f:
            sql_content = f.read()

        conn = sqlite3.connect(":memory:")
        try:
            conn.executescript(sql_content)
        except Exception:
            # If pragma or dialect issues, try executing table by table or parsing inserts
            return SQLEvidenceInspector._fallback_regex_parse(sql_content, file_id, captured_at)

        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cursor.fetchall()]

        for table in tables:
            if table in ["snapshot_scope"]:
                continue
            cursor.execute(f"PRAGMA table_info('{table}')")
            cols = [c[1] for c in cursor.fetchall()]
            
            cursor.execute(f"SELECT * FROM '{table}'")
            rows = cursor.fetchall()

            for row in rows:
                row_dict = dict(zip(cols, row))
                obs = SQLEvidenceInspector._extract_observation_from_row(
                    table, row_dict, file_id, captured_at
                )
                if obs:
                    observations.append(obs)

        conn.close()
        return observations

    @staticmethod
    def _extract_observation_from_row(
        table: str, row_dict: Dict[str, Any], file_id: str, captured_at: str
    ) -> Optional[Dict[str, Any]]:
        rid = row_dict.get("resource_id")
        
        # Check if row contains a payload string (JSON blob in replica tables)
        origin_sys = row_dict.get("origin_system") or row_dict.get("system_id")
        for k, v in row_dict.items():
            if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
                try:
                    payload = json.loads(v)
                    return SQLEvidenceInspector._extract_from_payload(
                        table, payload, file_id, captured_at, origin_sys
                    )
                except Exception:
                    pass

        # Identify system and category from table name
        sys_id = "account_service"
        cat = "USER_PROFILE"
        status = "FOUND"
        idents = set()

        if "account" in table or "customer_profiles" in table:
            sys_id = "account_service"
            cat = "USER_PROFILE"
            status = "FOUND"
        elif "search" in table:
            sys_id = "search_service"
            cat = "SEARCH_INDEX_ENTRY"
            status = "FOUND"
        elif "analytics" in table:
            sys_id = "analytics_platform"
            cat = "ANALYTICS_PROFILE"
            has_pii = any(row_dict.get(k) for k in ["email", "phone", "email_hash", "customer_reference", "user_id"])
            status = "IDENTIFIABLE" if has_pii else "ANONYMIZED"
        elif "support" in table:
            sys_id = "support_platform"
            cat = "SUPPORT_MESSAGE"
            has_pii = any(row_dict.get(k) for k in ["requester_email", "requester_name", "requester_phone"])
            status = "IDENTIFIABLE" if has_pii else "REDACTED"
        elif "export" in table:
            sys_id = "export_service"
            cat = "USER_EXPORT"
            status = "FOUND"
        elif "connector" in table:
            sys_id = "integration_service"
            cat = "DATA_FLOW"
            enabled = bool(row_dict.get("enabled", 1))
            status = "ACTIVE" if enabled else "DISABLED"
        elif "backup" in table:
            sys_id = "backup_service"
            cat = "BACKUP_ARCHIVE"
            restore_allowed = bool(row_dict.get("restore_allowed", 1))
            status = "ACTIVE" if restore_allowed else "BLOCKED"
        elif "audit" in table:
            sys_id = "security_service"
            cat = "SECURITY_AUDIT_LOG"
            status = "FOUND"

        for k, v in row_dict.items():
            if v and any(sub in k for sub in ["email", "user", "customer", "subject", "requester", "owner"]):
                idents.add(str(v).lower())

        if not rid:
            return None

        return {
            "file_id": file_id,
            "captured_at": captured_at,
            "system_id": sys_id,
            "resource_id": rid,
            "category": cat,
            "status": status,
            "user_identifiers": idents,
            "raw": row_dict
        }

    @staticmethod
    def _extract_from_payload(table: str, payload: dict, file_id: str, captured_at: str, override_sys: Optional[str] = None) -> Dict[str, Any]:
        rid = str(payload.get("resource_id", ""))
        sys_id = override_sys or "account_service"
        cat = "USER_PROFILE"
        status = "FOUND"
        idents = set()

        if "analytics" in sys_id or "analytics" in table or rid.startswith("analytics_"):
            sys_id = "analytics_platform"
            cat = "ANALYTICS_PROFILE"
            has_pii = any(payload.get(k) for k in ["email", "phone", "email_hash", "customer_reference", "user_id"])
            status = "IDENTIFIABLE" if has_pii else "ANONYMIZED"
        elif "support" in sys_id or "support" in table or rid.startswith("support_"):
            sys_id = "support_platform"
            cat = "SUPPORT_MESSAGE"
            has_pii = any(payload.get(k) for k in ["requester_email", "requester_name", "requester_phone"])
            status = "IDENTIFIABLE" if has_pii else "REDACTED"
        elif "search" in sys_id or "search" in table or rid.startswith("search_"):
            sys_id = "search_service"
            cat = "SEARCH_INDEX_ENTRY"
            status = "FOUND"
        elif "security" in sys_id or "audit" in table or rid.startswith("audit_record_"):
            sys_id = "security_service"
            cat = "SECURITY_AUDIT_LOG"
            status = "FOUND"
        elif rid.startswith("account_"):
            sys_id = "account_service"
            cat = "USER_PROFILE"
            status = "FOUND"

        def _extract_idents(obj: Any):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if v and any(sub in str(k).lower() for sub in ["email", "user", "customer", "subject", "requester"]):
                        idents.add(str(v).lower())
                    _extract_idents(v)
            elif isinstance(obj, list):
                for item in obj:
                    _extract_idents(item)

        _extract_idents(payload)

        return {
            "file_id": file_id,
            "captured_at": captured_at,
            "system_id": sys_id,
            "resource_id": rid,
            "category": cat,
            "status": status,
            "user_identifiers": idents,
            "raw": payload
        }

    @staticmethod
    def _fallback_regex_parse(sql_content: str, file_id: str, captured_at: str) -> List[Dict[str, Any]]:
        # Simple fallback parsing INSERT INTO statements if SQLite exec fails
        obs = []
        for line in sql_content.splitlines():
            line = line.strip()
            if not line.startswith("INSERT INTO"):
                continue
            m = re.match(r'INSERT INTO "?(\w+)"? VALUES\((.*?)\);', line)
            if m:
                table = m.group(1)
                vals_str = m.group(2)
                # extract quoted values
                vals = re.findall(r"'(.*?)'|NULL|(\d+)", vals_str)
                flat_vals = [v[0] if v[0] else v[1] for v in vals]
                if flat_vals:
                    rid = flat_vals[0]
                    idents = {v.lower() for v in flat_vals if "@" in v or "user_" in v}
                    obs.append({
                        "file_id": file_id,
                        "captured_at": captured_at,
                        "system_id": "account_service",
                        "resource_id": rid,
                        "category": "USER_PROFILE",
                        "status": "FOUND",
                        "user_identifiers": idents,
                        "raw": line
                    })
        return obs
