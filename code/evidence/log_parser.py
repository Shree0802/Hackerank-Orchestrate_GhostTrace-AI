"""Parser for server log streams, readback traces, and diagnostic observability exports."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

class LogEvidenceParser:
    """Extracts structured resource observations from various log formats with trace correlation."""

    @staticmethod
    def parse_file(file_path: Path, file_id: str, captured_at: str) -> List[Dict[str, Any]]:
        observations = []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = [l.strip() for l in f if l.strip()]

        # Pass 1: Collect identifiers by trace_id / requestId
        trace_idents: Dict[str, Set[str]] = {}
        for line in lines:
            tid = None
            if "trace_id=" in line:
                m = re.search(r'trace_id=([a-zA-Z0-9\-_]+)', line)
                if m:
                    tid = m.group(1)
            elif "requestId=" in line:
                m = re.search(r'requestId=([a-zA-Z0-9\-_]+)', line)
                if m:
                    tid = m.group(1)
            elif "{" in line and "}" in line:
                try:
                    data = json.loads(line[line.find("{"):line.rfind("}")+1])
                    tid = data.get("trace_id") or data.get("requestId")
                    if tid:
                        if tid not in trace_idents:
                            trace_idents[tid] = set()
                        for k, v in data.items():
                            if v and any(sub in str(k).lower() for sub in ["email", "user", "customer", "subject", "lookup_key", "correlation_key", "subject_ref"]):
                                trace_idents[tid].add(str(v).lower())
                except Exception:
                    pass

            if tid:
                if tid not in trace_idents:
                    trace_idents[tid] = set()
                # Extract any user/email identifiers in this line
                for m in re.finditer(r'(?:email|user|customer|subject|lookup_key|correlation_key|subject_key|subject_ref)=(".*?"|\S+)', line, re.IGNORECASE):
                    val = m.group(1).strip('"')
                    if val and val != "null":
                        trace_idents[tid].add(val.lower())

        # Pass 2: Parse observations, using completed events where available
        by_trace: Dict[str, Dict[str, Any]] = {}

        for line in lines:
            obs = LogEvidenceParser._parse_log_line(line, file_id, captured_at, trace_idents)
            if obs:
                tid = obs.get("trace_id")
                event = str(obs.get("event", ""))
                if tid:
                    if tid in by_trace:
                        # Preserve specific status if new is generic FOUND
                        old_stat = by_trace[tid].get("status")
                        if old_stat in ["IDENTIFIABLE", "NOT_FOUND", "REDACTED", "ANONYMIZED", "DISABLED", "BLOCKED"] and obs.get("status") == "FOUND":
                            obs["status"] = old_stat
                        # Merge identifiers
                        obs["user_identifiers"].update(by_trace[tid].get("user_identifiers", set()))
                    by_trace[tid] = obs
                else:
                    observations.append(obs)

        observations.extend(by_trace.values())
        return observations

    @staticmethod
    def _parse_log_line(
        line: str, file_id: str, captured_at: str, trace_idents: Dict[str, Set[str]]
    ) -> Optional[Dict[str, Any]]:
        # 1. JSON lines (e.g. structured_service_events_*.log)
        if "{" in line and "}" in line:
            json_part = line[line.find("{"):line.rfind("}")+1]
            try:
                data = json.loads(json_part)
                rid = data.get("resource_id")
                if rid:
                    sys_id = data.get("service") or data.get("logger") or "unknown"
                    event = data.get("event", "")
                    rows = data.get("rows")
                    http_status = data.get("http_status")
                    tid = data.get("trace_id") or data.get("requestId")
                    
                    status = "FOUND"
                    if rows == "0" or rows == 0 or http_status in ["404", 404]:
                        status = "NOT_FOUND"
                    elif data.get("integrity_check") == "passed" and (rows == "1" or rows == 1):
                        status = "PRESENT"

                    idents = set()
                    if tid and tid in trace_idents:
                        idents.update(trace_idents[tid])
                    for k, v in data.items():
                        if v and any(sub in k for sub in ["email", "user", "customer", "subject", "lookup_key"]):
                            idents.add(str(v).lower())

                    cat = LogEvidenceParser._infer_category(sys_id, rid)
                    sys_id = LogEvidenceParser._canonical_system_id(sys_id, rid)

                    return {
                        "file_id": file_id,
                        "captured_at": captured_at,
                        "system_id": sys_id,
                        "resource_id": rid,
                        "category": cat,
                        "status": status,
                        "user_identifiers": idents,
                        "trace_id": tid,
                        "event": event,
                        "raw": data
                    }
            except Exception:
                pass

        # 2. Key-value formatted lines (e.g. resource_lookup_trace_*.log, service_events_*.log)
        kv = {}
        for match in re.finditer(r'([a-zA-Z_0-9]+)=(".*?"|\S+)', line):
            k = match.group(1)
            v = match.group(2).strip('"')
            kv[k] = v

        rid = kv.get("resource_id")
        if not rid:
            return None

        sys_id = kv.get("service") or "unknown"
        if sys_id == "readback_collector":
            sys_id = "account_service"

        event = kv.get("event", "")
        tid = kv.get("trace_id") or kv.get("requestId")
        
        status = "FOUND"
        if kv.get("http_status") == "404" or kv.get("rows") == "0":
            status = "NOT_FOUND"
        elif "pii" in event or kv.get("matched_value"):
            status = "IDENTIFIABLE"
        elif "null" in kv.get("email", "") and "null" in kv.get("customer_reference", "") and ("analytics" in sys_id or rid.startswith("analytics_")):
            status = "ANONYMIZED"
        elif ("analytics" in sys_id or rid.startswith("analytics_")) and (kv.get("email") and kv.get("email") != "null"):
            status = "IDENTIFIABLE"
        elif ("support" in sys_id or rid.startswith("support_")) and (kv.get("requester_email") and kv.get("requester_email") != "null"):
            status = "IDENTIFIABLE"
        elif ("support" in sys_id or rid.startswith("support_")) and kv.get("requester_email") == "null":
            status = "REDACTED"
        elif kv.get("enabled") == "true":
            status = "ACTIVE"
        elif kv.get("enabled") == "false":
            status = "DISABLED"
        elif kv.get("restore_allowed") == "true" or kv.get("deletion_block") == "false" or kv.get("eligible") == "true":
            status = "ACTIVE"
        elif kv.get("restore_allowed") == "false" or kv.get("deletion_block") == "true":
            status = "BLOCKED"
        elif kv.get("integrity_check") == "passed" and (kv.get("rows") in ["1", 1] or "audit" in sys_id or rid.startswith("audit_record_")):
            status = "PRESENT"
        elif kv.get("result") == "hit" or kv.get("total_hits") == "1":
            status = "FOUND"

        idents = set()
        if tid and tid in trace_idents:
            idents.update(trace_idents[tid])
        for k, v in kv.items():
            if v and v != "null" and any(sub in k.lower() for sub in ["email", "user", "customer", "subject", "lookup_key", "correlation_key"]):
                idents.add(v.lower())

        cat = LogEvidenceParser._infer_category(sys_id, rid)
        sys_id = LogEvidenceParser._canonical_system_id(sys_id, rid)

        return {
            "file_id": file_id,
            "captured_at": captured_at,
            "system_id": sys_id,
            "resource_id": rid,
            "category": cat,
            "status": status,
            "user_identifiers": idents,
            "trace_id": tid,
            "event": event,
            "raw": line
        }

    @staticmethod
    def _canonical_system_id(sys_id: str, rid: str) -> str:
        if rid.startswith("account_"):
            return "account_service"
        elif rid.startswith("analytics_"):
            return "analytics_platform"
        elif rid.startswith("audit_record_"):
            return "security_service"
        elif rid.startswith("search_"):
            return "search_service"
        elif rid.startswith("support_"):
            return "support_platform"
        elif rid.startswith("data_flow_"):
            return "integration_service"
        elif rid.startswith("backup_"):
            return "backup_service"
        elif rid.startswith("tombstone_"):
            return "identity_service"
        elif rid.startswith("export_"):
            return "export_service"
        return sys_id

    @staticmethod
    def _infer_category(sys_id: str, rid: str) -> str:
        if rid.startswith("account_"):
            return "USER_PROFILE"
        elif rid.startswith("search_"):
            return "SEARCH_INDEX_ENTRY"
        elif rid.startswith("analytics_"):
            return "ANALYTICS_PROFILE"
        elif rid.startswith("support_"):
            return "SUPPORT_MESSAGE"
        elif rid.startswith("data_flow_"):
            return "DATA_FLOW"
        elif rid.startswith("backup_"):
            return "BACKUP_ARCHIVE"
        elif rid.startswith("audit_record_"):
            return "SECURITY_AUDIT_LOG"
        elif rid.startswith("tombstone_"):
            return "ACCOUNT_TOMBSTONE"
        elif rid.startswith("export_"):
            return "USER_EXPORT"
        return "UNKNOWN"
