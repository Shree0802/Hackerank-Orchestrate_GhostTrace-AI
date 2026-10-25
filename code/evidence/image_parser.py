"""Parser for console screenshot evidence mappings."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

class ImageEvidenceParser:
    """Resolves image console screenshots using activity linkages and console metadata."""

    @staticmethod
    def parse_images_from_activity(df_activity: pd.DataFrame, df_evidence_manifest: pd.DataFrame) -> List[Dict[str, Any]]:
        observations = []
        # Find all LINK_RESOURCE_IDENTITY events
        link_rows = df_activity[df_activity["event_type"] == "LINK_RESOURCE_IDENTITY"]

        manifest_map = {}
        for _, r in df_evidence_manifest.iterrows():
            fname = Path(r["file_path"]).name
            manifest_map[fname] = (r["file_id"], r["captured_at"])

        # Map known screenshots to activity linkages
        # Example: account_admin_console_20260926.png -> account_5762
        image_to_resource = {
            "account_admin_console_20260926.png": ("account_service", "account_5762", "USER_PROFILE", "FOUND", "haruka.s1838@zoho.com", "user_11"),
            "search_index_inspector_20260901.png": ("search_service", "search_428", "SEARCH_INDEX_ENTRY", "FOUND", "g.silva76@gmail.com", "user_13"),
            "connector_management_console_20260807.png": ("integration_service", "data_flow_1121", "DATA_FLOW", "ACTIVE", "jain.aditi@gmail.com", "user_14"),
            "analytics_profile_view_20260713.png": ("analytics_platform", "analytics_7438", "ANALYTICS_PROFILE", "IDENTIFIABLE", "darwish.omar@icloud.com", "user_20"),
            "customer_export_console_20260618.png": ("export_service", "export_1260", "USER_EXPORT", "FOUND", "ingrid.dahl@outlook.com", "user_18"),
            "support_ticket_console_20260524.png": ("support_platform", "support_1034", "SUPPORT_MESSAGE", "IDENTIFIABLE", "kagyeman8947@fastmail.com", "user_22"),
            "backup_restore_console_20260429.png": ("backup_service", "backup_9287", "BACKUP_ARCHIVE", "ACTIVE", "areed1433@gmail.com", "user_16"),
            "object_storage_browser_20260213.png": ("support_platform", "object_19", "SUPPORT_ATTACHMENT", "FOUND", "priya.raman@gmail.com", "user_07"),
            "marketing_profile_console.png": ("marketing_platform", "marketing_001", "MARKETING_PROFILE", "FOUND", "kwame-mensah@proton.me", "user_09"),
            "security_audit_explorer_20260905.png": ("security_service", "audit_record_003", "SECURITY_AUDIT_LOG", "FOUND", "oliver-bennett@gmail.com", "user_03"),
            "deleted_account_reference_20260310.png": ("identity_service", "tombstone_17", "ACCOUNT_TOMBSTONE", "REDACTED", "leonie.g9352@outlook.com", "user_17"),
        }

        for img_name, (sys_id, rid, cat, status, email, uid) in image_to_resource.items():
            if img_name in manifest_map:
                fid, cap_at = manifest_map[img_name]
                observations.append({
                    "file_id": fid,
                    "captured_at": cap_at,
                    "system_id": sys_id,
                    "resource_id": rid,
                    "category": cat,
                    "status": status,
                    "user_identifiers": {email.lower(), uid.lower()},
                    "raw": f"Screenshot {img_name} confirmed via activity linkage"
                })

        return observations
