"""Identity resolution engine resolving current and historical identifiers to stable user IDs."""

from typing import Dict, List, Optional
import pandas as pd
from code.identity.identity_graph import UserIdentity

class IdentityResolver:
    """Resolves identities across user_identities.csv and user_audit_log.csv."""

    def __init__(self, df_identities: pd.DataFrame, df_audit_log: pd.DataFrame):
        self.identities_by_id: Dict[str, UserIdentity] = {}
        self.email_to_user_id: Dict[str, str] = {}
        self._build_identity_graph(df_identities, df_audit_log)

    def _build_identity_graph(self, df_identities: pd.DataFrame, df_audit_log: pd.DataFrame):
        # 1. Ingest current snapshots
        for _, row in df_identities.iterrows():
            uid = str(row["user_id"]).strip()
            name = str(row["name"]).strip() if pd.notna(row["name"]) else None
            email = str(row["email"]).strip() if pd.notna(row["email"]) else None
            phone = str(row["phone"]).strip() if pd.notna(row["phone"]) else None
            ehash = str(row["email_hash"]).strip() if pd.notna(row["email_hash"]) else None
            up_at = str(row["updated_at"]).strip() if pd.notna(row["updated_at"]) else None

            u = UserIdentity(
                user_id=uid,
                current_name=name,
                current_email=email.lower() if email else None,
                current_phone=phone,
                current_hash=ehash,
                updated_at=up_at,
            )
            if email:
                u.all_emails.add(email.lower())
            if phone:
                u.all_phones.add(phone)
            if name:
                u.all_names.add(name)
            if ehash:
                u.all_hashes.add(ehash)

            self.identities_by_id[uid] = u
            if email:
                self.email_to_user_id[email.lower()] = uid

        # 2. Ingest historical audit log
        for _, row in df_audit_log.iterrows():
            uid = str(row["user_id"]).strip()
            if uid not in self.identities_by_id:
                continue
            u = self.identities_by_id[uid]
            aid = str(row["audit_id"]).strip()
            u.supporting_audit_ids.append(aid)

            field_name = str(row["field_name"]).strip().lower()
            old_val = str(row["old_value"]).strip() if pd.notna(row["old_value"]) else None
            new_val = str(row["new_value"]).strip() if pd.notna(row["new_value"]) else None

            if field_name == "email":
                if old_val:
                    u.all_emails.add(old_val.lower())
                    self.email_to_user_id[old_val.lower()] = uid
                if new_val:
                    u.all_emails.add(new_val.lower())
                    self.email_to_user_id[new_val.lower()] = uid
            elif field_name == "phone":
                if old_val:
                    u.all_phones.add(old_val)
                if new_val:
                    u.all_phones.add(new_val)
            elif field_name == "name":
                if old_val:
                    u.all_names.add(old_val)
                if new_val:
                    u.all_names.add(new_val)
            elif field_name in ["email_hash", "hash"]:
                if old_val:
                    u.all_hashes.add(old_val.lower())
                if new_val:
                    u.all_hashes.add(new_val.lower())

    def resolve_email(self, email: str) -> Optional[UserIdentity]:
        """Resolve an email (current or historical) to the corresponding UserIdentity."""
        if not email:
            return None
        clean_email = email.strip().lower()
        uid = self.email_to_user_id.get(clean_email)
        if uid:
            return self.identities_by_id.get(uid)
        return None

    def get_user_by_id(self, user_id: str) -> Optional[UserIdentity]:
        """Retrieve user identity directly by stable user_id."""
        return self.identities_by_id.get(user_id.strip())
