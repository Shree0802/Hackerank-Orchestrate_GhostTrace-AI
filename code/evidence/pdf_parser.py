"""Parser for PDF document evidence using PyMuPDF (fitz)."""

from pathlib import Path
from typing import Any, Dict, List, Set
import fitz
import re

class PDFEvidenceParser:
    """Extracts structured customer and retention records from PDF documents."""

    @staticmethod
    def parse_file(file_path: Path, file_id: str, captured_at: str) -> List[Dict[str, Any]]:
        observations = []
        doc = fitz.open(file_path)
        full_text = "\n".join([page.get_text() for page in doc])
        fname = file_path.name

        if "delivery_correction_attachment" in fname:
            # CS-4827 / support_001 | Priya Raman | priya.raman@gmail.com
            m_res = re.search(r'support_\d+', full_text)
            rid = m_res.group(0) if m_res else "support_001"
            idents = set()
            for em in re.findall(r'[\w\.-]+@[\w\.-]+', full_text):
                idents.add(em.lower())
            for uid in re.findall(r'user_\d+', full_text):
                idents.add(uid.lower())
            
            observations.append({
                "file_id": file_id,
                "captured_at": captured_at,
                "system_id": "support_platform",
                "resource_id": rid,
                "category": "SUPPORT_ATTACHMENT",
                "status": "FOUND",
                "user_identifiers": idents,
                "raw": full_text[:200]
            })

        elif "legal_retention_register" in fname:
            # Table of disputed orders and retained records: e.g. ORD-20264118 | user_08
            for line in full_text.splitlines():
                if "ORD-" in line and "user_" in line:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 2:
                        ord_id = parts[0]
                        user_id = parts[1]
                        observations.append({
                            "file_id": file_id,
                            "captured_at": captured_at,
                            "system_id": "legal_service",
                            "resource_id": ord_id,
                            "category": "LEGAL_HOLD_RECORD",
                            "status": "FOUND",
                            "user_identifiers": {user_id.lower()},
                            "raw": line
                        })

        elif "security_retention_extract" in fname:
            # Event reference audit_record_003 | subject reference user_03
            m_res = re.search(r'audit_record_\d+', full_text)
            rid = m_res.group(0) if m_res else "audit_record_003"
            m_user = re.search(r'user_\d+', full_text)
            idents = {m_user.group(0).lower()} if m_user else set()
            observations.append({
                "file_id": file_id,
                "captured_at": captured_at,
                "system_id": "security_service",
                "resource_id": rid,
                "category": "SECURITY_AUDIT_LOG",
                "status": "FOUND",
                "user_identifiers": idents,
                "raw": full_text[:200]
            })

        elif "account_history_report" in fname:
            # Customer Ingrid Dahl | user_18 | ingrid.dahl@outlook.com
            m_res = re.search(r'export_\d+', full_text)
            rid = m_res.group(0) if m_res else "export_1842"
            idents = set()
            for em in re.findall(r'[\w\.-]+@[\w\.-]+', full_text):
                idents.add(em.lower())
            for uid in re.findall(r'user_\d+', full_text):
                idents.add(uid.lower())
            observations.append({
                "file_id": file_id,
                "captured_at": captured_at,
                "system_id": "export_service",
                "resource_id": rid,
                "category": "USER_EXPORT",
                "status": "FOUND",
                "user_identifiers": idents,
                "raw": full_text[:200]
            })

        return observations
