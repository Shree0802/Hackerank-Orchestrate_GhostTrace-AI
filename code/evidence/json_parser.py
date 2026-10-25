"""Parser for JSON and structured text records in the evidence dataset."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

class JSONEvidenceParser:
    """Parses various JSON snapshot and handover formats."""

    @staticmethod
    def parse_file(file_path: Path, file_id: str, captured_at: str) -> List[Dict[str, Any]]:
        observations = []
        path_str = str(file_path)
        
        # Handle structured text handover file
        if path_str.endswith(".txt"):
            return JSONEvidenceParser._parse_handover_txt(file_path, file_id, captured_at)
            
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        fname = file_path.name
        if "service_resource_export" in fname:
            observations.extend(JSONEvidenceParser._parse_service_resource_export(data, file_id, captured_at))
        elif "customer_data_snapshot_bundle" in fname:
            observations.extend(JSONEvidenceParser._parse_snapshot_bundle(data, file_id, captured_at))
        elif "customer_analytics_report" in fname:
            observations.extend(JSONEvidenceParser._parse_analytics_report(data, file_id, captured_at))
        elif "customer_export_jobs" in fname:
            observations.extend(JSONEvidenceParser._parse_export_jobs(data, file_id, captured_at))
        elif "connector_configurations" in fname:
            observations.extend(JSONEvidenceParser._parse_connector_configs(data, file_id, captured_at))
        elif "security_audit_ledger" in fname:
            observations.extend(JSONEvidenceParser._parse_security_ledger(data, file_id, captured_at))
        elif "customer_export_manifest" in fname:
            observations.extend(JSONEvidenceParser._parse_export_manifest(data, file_id, captured_at))
        else:
            # Generic JSON records fallback
            if isinstance(data, dict) and "records" in data:
                observations.extend(JSONEvidenceParser._parse_generic_records(data["records"], file_id, captured_at))
        return observations

    @staticmethod
    def _parse_service_resource_export(data: dict, file_id: str, captured_at: str) -> List[Dict[str, Any]]:
        obs = []
        exports = data.get("service_exports", {})
        
        # 1. account_service
        for item in exports.get("account_service", {}).get("profile_lookups", []):
            rid = item.get("resource_id")
            status_code = item.get("status_code", 200)
            status = "NOT_FOUND" if status_code == 404 or item.get("profile") is None else "FOUND"
            obs.append({
                "file_id": file_id,
                "captured_at": captured_at,
                "system_id": "account_service",
                "resource_id": rid,
                "category": "USER_PROFILE",
                "status": status,
                "user_identifiers": set(),
                "raw": item
            })

        # 2. analytics_platform
        for item in exports.get("analytics_platform", {}).get("profiles", []):
            rid = item.get("resource_id")
            has_pii = any(item.get(k) for k in ["email", "phone", "email_hash", "customer_reference"])
            status = "IDENTIFIABLE" if has_pii else "ANONYMIZED"
            idents = {str(item[k]).lower() for k in ["email", "customer_reference"] if item.get(k)}
            obs.append({
                "file_id": file_id,
                "captured_at": captured_at,
                "system_id": "analytics_platform",
                "resource_id": rid,
                "category": "ANALYTICS_PROFILE",
                "status": status,
                "user_identifiers": idents,
                "raw": item
            })

        # 3. backup_service
        for item in exports.get("backup_service", {}).get("restore_entries", []):
            rid = item.get("resource_id")
            restore_allowed = item.get("restore_allowed", False)
            status = "ACTIVE" if restore_allowed else "BLOCKED"
            idents = {str(item[k]).lower() for k in ["customer_email", "customer_reference"] if item.get(k)}
            obs.append({
                "file_id": file_id,
                "captured_at": captured_at,
                "system_id": "backup_service",
                "resource_id": rid,
                "category": "BACKUP_ARCHIVE",
                "status": status,
                "user_identifiers": idents,
                "raw": item
            })

        # 4. export_service
        for item in exports.get("export_service", {}).get("exports", []):
            rid = item.get("resource_id")
            idents = {str(item[k]).lower() for k in ["owner_email", "customer_reference"] if item.get(k)}
            obs.append({
                "file_id": file_id,
                "captured_at": captured_at,
                "system_id": "export_service",
                "resource_id": rid,
                "category": "USER_EXPORT",
                "status": "FOUND",
                "user_identifiers": idents,
                "raw": item
            })

        # 5. integration_service
        for item in exports.get("integration_service", {}).get("connectors", []):
            rid = item.get("resource_id")
            enabled = item.get("enabled", False)
            status = "ACTIVE" if enabled else "DISABLED"
            idents = {str(item[k]).lower() for k in ["customer_email", "customer_reference"] if item.get(k)}
            obs.append({
                "file_id": file_id,
                "captured_at": captured_at,
                "system_id": "integration_service",
                "resource_id": rid,
                "category": "DATA_FLOW",
                "status": status,
                "user_identifiers": idents,
                "raw": item
            })

        # 6. search_service
        for item in exports.get("search_service", {}).get("index_queries", []):
            rid = item.get("resource_id")
            total = item.get("hits", {}).get("total", 0)
            status = "FOUND" if total > 0 else "NOT_FOUND"
            idents = set()
            for doc in item.get("hits", {}).get("documents", []):
                for k in ["email", "customer_reference"]:
                    if doc.get(k):
                        idents.add(str(doc[k]).lower())
            if item.get("query"):
                idents.add(str(item["query"]).lower())
            obs.append({
                "file_id": file_id,
                "captured_at": captured_at,
                "system_id": "search_service",
                "resource_id": rid,
                "category": "SEARCH_INDEX_ENTRY",
                "status": status,
                "user_identifiers": idents,
                "raw": item
            })

        # 7. security_service
        for item in exports.get("security_service", {}).get("audit_records", []):
            rid = item.get("resource_id")
            idents = {str(item["subject_reference"]).lower()} if item.get("subject_reference") else set()
            obs.append({
                "file_id": file_id,
                "captured_at": captured_at,
                "system_id": "security_service",
                "resource_id": rid,
                "category": "SECURITY_AUDIT_LOG",
                "status": "FOUND",
                "user_identifiers": idents,
                "raw": item
            })

        # 8. support_platform
        for item in exports.get("support_platform", {}).get("tickets", []):
            rid = item.get("resource_id")
            has_pii = any(item.get(k) for k in ["requester_email", "requester_name", "requester_phone"])
            status = "IDENTIFIABLE" if has_pii else "REDACTED"
            idents = {str(item[k]).lower() for k in ["requester_email", "customer_reference"] if item.get(k)}
            obs.append({
                "file_id": file_id,
                "captured_at": captured_at,
                "system_id": "support_platform",
                "resource_id": rid,
                "category": "SUPPORT_MESSAGE",
                "status": status,
                "user_identifiers": idents,
                "raw": item
            })

        return obs

    @staticmethod
    def _parse_snapshot_bundle(data: dict, file_id: str, captured_at: str) -> List[Dict[str, Any]]:
        obs = []
        for snap in data.get("snapshots", []):
            store = snap.get("data_store")
            coll = snap.get("collection")
            records = snap.get("records", [])

            if store == "account_service":
                for r in records:
                    rid = r.get("resource_id")
                    idents = {str(r[k]).lower() for k in ["email", "user_id", "customer_reference"] if r.get(k)}
                    obs.append({
                        "file_id": file_id,
                        "captured_at": captured_at,
                        "system_id": "account_service",
                        "resource_id": rid,
                        "category": "USER_PROFILE",
                        "status": "FOUND",
                        "user_identifiers": idents,
                        "raw": r
                    })

            elif store == "identity_service" and coll == "deleted_customer_references":
                for r in records:
                    rid = r.get("resource_id")
                    has_pii = any(r.get(k) for k in ["name", "email", "phone", "email_hash"])
                    status = "IDENTIFIABLE" if has_pii else "REDACTED"
                    idents = {str(r[k]).lower() for k in ["email", "subject_reference", "user_id"] if r.get(k)}
                    obs.append({
                        "file_id": file_id,
                        "captured_at": captured_at,
                        "system_id": "identity_service",
                        "resource_id": rid,
                        "category": "ACCOUNT_TOMBSTONE",
                        "status": status,
                        "user_identifiers": idents,
                        "raw": r
                    })

            elif store == "security_service":
                for r in records:
                    rid = r.get("resource_id")
                    idents = {str(r[k]).lower() for k in ["subject_reference", "user_id"] if r.get(k)}
                    obs.append({
                        "file_id": file_id,
                        "captured_at": captured_at,
                        "system_id": "security_service",
                        "resource_id": rid,
                        "category": "SECURITY_AUDIT_LOG",
                        "status": "FOUND",
                        "user_identifiers": idents,
                        "raw": r
                    })
        return obs

    @staticmethod
    def _parse_handover_txt(file_path: Path, file_id: str, captured_at: str) -> List[Dict[str, Any]]:
        obs = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or not line.startswith("- "):
                    continue
                parts = [p.strip() for p in line[2:].split("|")]
                if len(parts) >= 6:
                    ts, sys_id, rid, cat, status, user_ref = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
                    idents = {user_ref.lower()} if user_ref and "no direct" not in user_ref.lower() else set()
                    obs.append({
                        "file_id": file_id,
                        "captured_at": captured_at,
                        "system_id": sys_id,
                        "resource_id": rid,
                        "category": cat,
                        "status": status,
                        "user_identifiers": idents,
                        "raw": line
                    })
        return obs

    @staticmethod
    def _parse_analytics_report(data: dict, file_id: str, captured_at: str) -> List[Dict[str, Any]]:
        obs = []
        for r in data.get("records", []):
            rid = r.get("resource_id")
            has_pii = any(r.get(k) for k in ["email", "phone", "email_hash", "customer_reference", "user_id"])
            status = "IDENTIFIABLE" if has_pii else "ANONYMIZED"
            idents = {str(r[k]).lower() for k in ["email", "customer_reference", "user_id"] if r.get(k)}
            obs.append({
                "file_id": file_id,
                "captured_at": captured_at,
                "system_id": "analytics_platform",
                "resource_id": rid,
                "category": "ANALYTICS_PROFILE",
                "status": status,
                "user_identifiers": idents,
                "raw": r
            })
        return obs

    @staticmethod
    def _parse_export_jobs(data: dict, file_id: str, captured_at: str) -> List[Dict[str, Any]]:
        obs = []
        for r in data.get("records", []):
            rid = r.get("resource_id")
            idents = {str(r[k]).lower() for k in ["owner_email", "customer_reference", "user_id"] if r.get(k)}
            obs.append({
                "file_id": file_id,
                "captured_at": captured_at,
                "system_id": "export_service",
                "resource_id": rid,
                "category": "USER_EXPORT",
                "status": "FOUND",
                "user_identifiers": idents,
                "raw": r
            })
        return obs

    @staticmethod
    def _parse_connector_configs(data: dict, file_id: str, captured_at: str) -> List[Dict[str, Any]]:
        obs = []
        for r in data.get("records", []):
            rid = r.get("resource_id")
            enabled = r.get("enabled", False)
            status = "ACTIVE" if enabled else "DISABLED"
            idents = {str(r[k]).lower() for k in ["customer_email", "customer_reference", "user_id"] if r.get(k)}
            obs.append({
                "file_id": file_id,
                "captured_at": captured_at,
                "system_id": "integration_service",
                "resource_id": rid,
                "category": "DATA_FLOW",
                "status": status,
                "user_identifiers": idents,
                "raw": r
            })
        return obs

    @staticmethod
    def _parse_security_ledger(data: dict, file_id: str, captured_at: str) -> List[Dict[str, Any]]:
        obs = []
        for r in data.get("records", []):
            rid = r.get("resource_id")
            idents = {str(r[k]).lower() for k in ["subject_reference", "user_id"] if r.get(k)}
            obs.append({
                "file_id": file_id,
                "captured_at": captured_at,
                "system_id": "security_service",
                "resource_id": rid,
                "category": "SECURITY_AUDIT_LOG",
                "status": "FOUND",
                "user_identifiers": idents,
                "raw": r
            })
        return obs

    @staticmethod
    def _parse_export_manifest(data: dict, file_id: str, captured_at: str) -> List[Dict[str, Any]]:
        obs = []
        for r in data.get("records", []):
            rid = r.get("resource_id")
            idents = {str(r[k]).lower() for k in ["owner_email", "customer_reference", "user_id"] if r.get(k)}
            obs.append({
                "file_id": file_id,
                "captured_at": captured_at,
                "system_id": "export_service",
                "resource_id": rid,
                "category": "USER_EXPORT",
                "status": "FOUND",
                "user_identifiers": idents,
                "raw": r
            })
        return obs

    @staticmethod
    def _parse_generic_records(records: list, file_id: str, captured_at: str) -> List[Dict[str, Any]]:
        obs = []
        for r in records:
            if not isinstance(r, dict):
                continue
            rid = r.get("resource_id")
            if not rid:
                continue
            idents = set()
            for k, v in r.items():
                if any(sub in k for sub in ["email", "user", "customer", "subject", "owner"]):
                    if v:
                        idents.add(str(v).lower())
            obs.append({
                "file_id": file_id,
                "captured_at": captured_at,
                "system_id": r.get("system_id", "unknown"),
                "resource_id": rid,
                "category": r.get("category", "UNKNOWN"),
                "status": "FOUND",
                "user_identifiers": idents,
                "raw": r
            })
        return obs
