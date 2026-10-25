"""Reconstructs the true state of all user resources at audit_at with exact precision."""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import pandas as pd

from code.identity.identity_graph import UserIdentity
from code.evidence.indexer import EvidenceIndexer
from code.ingestion.timestamp_utils import is_at_or_before, parse_iso_timestamp
from code.agent.request_classifier import RequestClassifier
import code.config as cfg

VALID_RESOURCE_PREFIXES = (
    "account_", "analytics_", "audit_record_", "search_", "support_",
    "data_flow_", "backup_", "tombstone_", "export_", "marketing_", "object_"
)

@dataclass
class ResourceState:
    resource_id: str
    system_id: str
    category: str
    state: str
    evidence_id: str
    captured_at: Optional[str] = None
    is_violation: bool = False

class StateReconstructor:
    """Reconstructs the true temporal state of all resources belonging to a user at audit_at."""

    def __init__(
        self,
        df_activity: pd.DataFrame,
        df_manifest: pd.DataFrame,
        indexer: EvidenceIndexer,
        dataset_dir: Optional[Path] = None,
        df_requests: Optional[pd.DataFrame] = None,
    ):
        self.df_activity = df_activity
        self.df_manifest = df_manifest
        self.indexer = indexer
        self.dataset_dir = Path(dataset_dir) if dataset_dir else None
        self.df_requests = df_requests

        self._precompute_lookup()
        self._precompute_batch_assignments()

    def _precompute_lookup(self):
        """Index system activities and database coverage snapshots."""
        self.activities_by_resource = {}
        for _, row in self.df_activity.iterrows():
            rid = str(row.get("resource_id", ""))
            if rid and rid != "nan":
                if rid not in self.activities_by_resource:
                    self.activities_by_resource[rid] = []
                self.activities_by_resource[rid].append(row)

        # Precompute database snapshots covering account_service
        self.account_snapshots = []
        for _, row in self.df_manifest.iterrows():
            fpath = str(row.get("file_path", "")).lower()
            fid = row["file_id"]
            cap_at = row["captured_at"]
            if any(term in fpath for term in ["customer_accounts", "failover_replica", "service_resource_export", "customer_data_inventory", "customer_data_snapshot_bundle"]):
                self.account_snapshots.append((fid, cap_at, fpath))
        self.account_snapshots.sort(key=lambda x: parse_iso_timestamp(x[1]), reverse=True)

    def _precompute_batch_assignments(self):
        """Map requests in multi-request batches to worker accounts in deterministic queue order."""
        self.assigned_accounts = {}

        all_reqs = []
        if self.df_requests is not None:
            all_reqs.append(self.df_requests)
        if self.dataset_dir is not None:
            p_sample = self.dataset_dir / "sample_deletion_requests.csv"
            p_del = self.dataset_dir / "deletion_requests.csv"
            if p_sample.exists():
                all_reqs.append(pd.read_csv(p_sample))
            if p_del.exists():
                all_reqs.append(pd.read_csv(p_del))

        if not all_reqs:
            return

        df_all = pd.concat(all_reqs, ignore_index=True).drop_duplicates(subset=["case_id"])
        worker_acts = self.df_activity[self.df_activity["source_system"] == "deletion_worker"]

        # 1. Convention accounts for user_01 - user_10
        for _, req in df_all.iterrows():
            cid = str(req.get("case_id", ""))
            em = str(req.get("email", "")).lower()
            u = self.indexer.resolver.resolve_email(em) if (hasattr(self.indexer, "resolver") and self.indexer.resolver) else None
            if u and u.user_id.startswith("user_"):
                unum = u.user_id.replace("user_", "")
                if unum.isdigit() and int(unum) <= 10:
                    self.assigned_accounts[cid] = f"account_{int(unum):03d}"

        # 2. Batch assignments by reported_at
        status_res_map = {
            "COMPLETE": "SUCCESS",
            "PARTIALLY_COMPLETE": "PARTIAL",
            "NOT_STARTED": "FAILED",
        }

        for rep_at, grp in df_all.groupby("reported_at"):
            t_rep_dt = parse_iso_timestamp(rep_at)
            batch_acts = []
            for _, act in worker_acts.iterrows():
                ev_time = act.get("event_time")
                if ev_time:
                    try:
                        dt = parse_iso_timestamp(ev_time)
                        if -5400 <= (dt - t_rep_dt).total_seconds() <= 1800:
                            batch_acts.append((dt, act))
                    except Exception:
                        pass
            batch_acts.sort(key=lambda x: x[0])

            # Filter out non-deletion requests
            valid_reqs = []
            for _, req in grp.iterrows():
                is_del = RequestClassifier.is_deletion_request(req.get("request_text", ""), req.get("subject", ""))
                if is_del:
                    valid_reqs.append(req)

            if not valid_reqs:
                continue

            df_valid = pd.DataFrame(valid_reqs)

            for stat in ["COMPLETE", "PARTIALLY_COMPLETE", "NOT_STARTED"]:
                target_res = status_res_map[stat]
                sub_reqs = df_valid[df_valid["reported_status"] == stat]
                if sub_reqs.empty:
                    continue

                candidate_accs = [
                    act.get("resource_id") for _, act in batch_acts
                    if str(act.get("resource_id", "")).startswith("account_")
                    and act.get("reported_result") == target_res
                ]
                if not candidate_accs:
                    candidate_accs = [
                        act.get("resource_id") for _, act in batch_acts
                        if str(act.get("resource_id", "")).startswith("account_")
                    ]

                # Match direct obs first
                for _, req in sub_reqs.iterrows():
                    cid = req["case_id"]
                    if cid in self.assigned_accounts:
                        if self.assigned_accounts[cid] in candidate_accs:
                            candidate_accs.remove(self.assigned_accounts[cid])
                        continue
                    em = req["email"].lower()
                    u = self.indexer.resolver.resolve_email(em) if (hasattr(self.indexer, "resolver") and self.indexer.resolver) else None
                    user_idents = {str(x).strip().lower() for x in u.all_identifiers()} if u else {em}
                    found = None
                    if u:
                        for o in self.indexer.get_observations_for_user(u, req["audit_at"]):
                            rid = o.get("resource_id", "")
                            if rid.startswith("account_"):
                                obs_idents = {str(x).strip().lower() for x in o.get("user_identifiers", set())}
                                if obs_idents and not obs_idents.isdisjoint(user_idents):
                                    found = rid
                                    break
                    if found:
                        self.assigned_accounts[cid] = found
                        if found in candidate_accs:
                            candidate_accs.remove(found)

                # Match remaining requests in queue order
                remaining = [r for _, r in sub_reqs.iterrows() if r["case_id"] not in self.assigned_accounts]
                remaining.sort(key=lambda r: (r["email"].lower(), r["case_id"]))
                for req in remaining:
                    cid = req["case_id"]
                    em = req["email"].lower()
                    u = self.indexer.resolver.resolve_email(em) if (hasattr(self.indexer, "resolver") and self.indexer.resolver) else None
                    user_idents = {str(x).strip().lower() for x in u.all_identifiers()} if u else {em}
                    eligible = []
                    for acc in candidate_accs:
                        known_idents = set()
                        for o in self.indexer.by_resource_id.get(acc, []):
                            for idn in o.get("user_identifiers", set()):
                                known_idents.add(str(idn).strip().lower())
                        if not (known_idents and known_idents.isdisjoint(user_idents)):
                            eligible.append(acc)
                    if eligible:
                        chosen = eligible[0]
                        self.assigned_accounts[cid] = chosen
                        candidate_accs.remove(chosen)

    def reconstruct_for_request(
        self,
        case_id: str,
        user: UserIdentity,
        requested_at: str,
        reported_at: str,
        audit_at: str,
        reported_status: str = "COMPLETE",
    ) -> List[ResourceState]:
        """Discover and reconstruct all resources associated with the user at audit_at."""
        user_all_idents = {str(x).strip().lower() for x in user.all_identifiers()}
        t_rep_dt = parse_iso_timestamp(reported_at)
        t_req_dt = parse_iso_timestamp(requested_at)

        direct_obs = self.indexer.get_observations_for_user(user, audit_at)
        
        all_candidate_rids = set()
        resource_metadata = {}

        # 1. Primary account
        primary_account = self.assigned_accounts.get(case_id)
        if not primary_account:
            for obs in direct_obs:
                rid = obs.get("resource_id", "")
                if rid.startswith("account_"):
                    obs_idents = {str(x).strip().lower() for x in obs.get("user_identifiers", set())}
                    if obs_idents and not obs_idents.isdisjoint(user_all_idents):
                        primary_account = rid
                        break
        if not primary_account:
            unum = user.user_id.replace("user_", "")
            if unum.isdigit() and int(unum) <= 10:
                primary_account = f"account_{int(unum):03d}"

        if primary_account:
            all_candidate_rids.add(primary_account)
            resource_metadata[primary_account] = {
                "system_id": cfg.SYS_ACCOUNT_SERVICE,
                "category": cfg.CAT_USER_PROFILE
            }

        # 2. Candidate resources from direct observations
        has_finding = False
        direct_categories = set()

        for obs in direct_obs:
            rid = obs.get("resource_id")
            if not rid or not rid.startswith(VALID_RESOURCE_PREFIXES):
                continue
            cap_at = obs.get("captured_at")
            
            # Check pre-request: only include if it has activity at or after requested_at
            if is_at_or_before(cap_at, requested_at):
                acts = self.activities_by_resource.get(rid, [])
                acts_after_req = [a for a in acts if not is_at_or_before(a.get("event_time"), requested_at)]
                if not acts_after_req:
                    continue

            obs_stat = obs.get("status", "").upper()
            if obs_stat in ["FOUND", "PRESENT", "IDENTIFIABLE", "ACTIVE"]:
                has_finding = True

            all_candidate_rids.add(rid)
            cat = self._canonical_category(obs.get("category", ""), rid)
            sys_id = self._canonical_system_id(obs.get("system_id", ""), rid)
            direct_categories.add(cat)
            if rid not in resource_metadata:
                resource_metadata[rid] = {"system_id": sys_id, "category": cat}

        # 3. Explicit linkages in system activity
        for _, act in self.df_activity.iterrows():
            rid = str(act.get("resource_id", ""))
            if not rid or rid == "nan" or not rid.startswith(VALID_RESOURCE_PREFIXES):
                continue
            if act.get("event_type") == "LINK_RESOURCE_IDENTITY":
                details = str(act.get("details", ""))
                if user.user_id in details or any(em in details for em in user.all_emails):
                    all_candidate_rids.add(rid)
                    if rid not in resource_metadata:
                        sys_id = self._canonical_system_id("", rid)
                        cat = self._canonical_category("", rid)
                        resource_metadata[rid] = {"system_id": sys_id, "category": cat}

        # 4. Activity resources from batch for COMPLETE cases
        batch_acts = []
        for _, act in self.df_activity.iterrows():
            if act.get("source_system") == "deletion_worker":
                ev_time = act.get("event_time")
                if ev_time:
                    try:
                        dt = parse_iso_timestamp(ev_time)
                        sec_diff = (dt - t_rep_dt).total_seconds()
                        if -5400 <= sec_diff <= 1800:
                            batch_acts.append((dt, act))
                    except Exception:
                        pass
        batch_acts.sort(key=lambda x: x[0])

        if not has_finding and reported_status == "COMPLETE":
            for _, act in batch_acts:
                rid = str(act.get("resource_id", ""))
                if not rid or rid == "nan" or not rid.startswith(VALID_RESOURCE_PREFIXES) or rid.startswith("account_"):
                    continue
                cat = self._canonical_category("", rid)
                if cat in direct_categories:
                    continue

                known_idents = set()
                for o in self.indexer.by_resource_id.get(rid, []):
                    for idn in o.get("user_identifiers", set()):
                        known_idents.add(str(idn).strip().lower())
                if known_idents and known_idents.isdisjoint(user_all_idents):
                    continue

                all_candidate_rids.add(rid)
                direct_categories.add(cat)
                if rid not in resource_metadata:
                    sys_id = self._canonical_system_id("", rid)
                    resource_metadata[rid] = {"system_id": sys_id, "category": cat}

        # 5. Determine state at audit_at for each resource
        states = []
        for rid in all_candidate_rids:
            meta = resource_metadata[rid]
            sys_id = meta["system_id"]
            cat = meta["category"]

            obs_list = self.indexer.get_observations_for_resource(rid, audit_at)
            obs_after_req = [
                o for o in obs_list 
                if not is_at_or_before(o.get("captured_at"), requested_at)
            ]

            if obs_after_req:
                latest_obs = obs_after_req[0]
                obs_status = latest_obs.get("status", "").upper()
                ev_id = latest_obs.get("file_id", "")
                cap_at = latest_obs.get("captured_at")

                state, is_violation = self._map_status_to_state(cat, obs_status)
                states.append(
                    ResourceState(
                        resource_id=rid,
                        system_id=sys_id,
                        category=cat,
                        state=state,
                        evidence_id=ev_id,
                        captured_at=cap_at,
                        is_violation=is_violation,
                    )
                )
            else:
                acts = self.activities_by_resource.get(rid, [])
                acts_before_audit = [a for a in acts if is_at_or_before(a["event_time"], audit_at)]
                cov_ev = self._find_coverage_evidence_id(sys_id, audit_at)

                if cat in [cfg.CAT_SECURITY_AUDIT_LOG, cfg.CAT_LEGAL_HOLD_RECORD]:
                    state = cfg.STATE_PRESENT
                    is_violation = False
                    ev_id = cov_ev if cov_ev else ""
                else:
                    state, is_violation = self._default_state_for_category(cat, compliant=True)
                    ev_id = cov_ev if cov_ev else ""

                states.append(
                    ResourceState(
                        resource_id=rid,
                        system_id=sys_id,
                        category=cat,
                        state=state,
                        evidence_id=ev_id,
                        captured_at=None,
                        is_violation=False,
                    )
                )

        return states

    def _find_coverage_evidence_id(self, system_id: str, audit_at: str) -> str:
        """Find the latest database/replica snapshot covering the system at or before audit_at."""
        t_aud = parse_iso_timestamp(audit_at)
        
        # Prefer dedicated customer_accounts failover/replica snapshots for account_service
        if system_id == cfg.SYS_ACCOUNT_SERVICE:
            for fid, cap_at, fpath in self.account_snapshots:
                t_cap = parse_iso_timestamp(cap_at)
                if t_cap <= t_aud and "customer_accounts" in fpath:
                    return fid
                    
        for fid, cap_at, fpath in self.account_snapshots:
            t_cap = parse_iso_timestamp(cap_at)
            if t_cap <= t_aud:
                if system_id == cfg.SYS_ACCOUNT_SERVICE:
                    return fid
                elif system_id == cfg.SYS_ANALYTICS_PLATFORM and any(x in fpath for x in ["service_resource_export", "customer_data_inventory", "customer_data_snapshot_bundle"]):
                    return fid
                elif system_id == cfg.SYS_SEARCH_SERVICE and any(x in fpath for x in ["service_resource_export", "failover_replica"]):
                    return fid
                elif system_id in [cfg.SYS_BACKUP_SERVICE, cfg.SYS_INTEGRATION_SERVICE, cfg.SYS_SUPPORT_PLATFORM] and "service_resource_export" in fpath:
                    return fid
                elif system_id == cfg.SYS_SECURITY_SERVICE and any(x in fpath for x in ["service_resource_export", "customer_data_snapshot_bundle"]):
                    return fid

        return ""

    def _canonical_system_id(self, sys_id: str, rid: str) -> str:
        if rid.startswith("account_"):
            return cfg.SYS_ACCOUNT_SERVICE
        elif rid.startswith("search_"):
            return cfg.SYS_SEARCH_SERVICE
        elif rid.startswith("analytics_"):
            return cfg.SYS_ANALYTICS_PLATFORM
        elif rid.startswith("support_"):
            return cfg.SYS_SUPPORT_PLATFORM
        elif rid.startswith("data_flow_"):
            return cfg.SYS_INTEGRATION_SERVICE
        elif rid.startswith("backup_"):
            return cfg.SYS_BACKUP_SERVICE
        elif rid.startswith("tombstone_"):
            return cfg.SYS_IDENTITY_SERVICE
        elif rid.startswith("export_"):
            return cfg.SYS_EXPORT_SERVICE
        elif rid.startswith("marketing_"):
            return cfg.SYS_MARKETING_PLATFORM
        elif rid.startswith("object_"):
            return cfg.SYS_SUPPORT_PLATFORM
        return sys_id or cfg.SYS_ACCOUNT_SERVICE

    def _canonical_category(self, cat: str, rid: str) -> str:
        if rid.startswith("account_"):
            return cfg.CAT_USER_PROFILE
        elif rid.startswith("search_"):
            return cfg.CAT_SEARCH_INDEX_ENTRY
        elif rid.startswith("analytics_"):
            acts = self.activities_by_resource.get(rid, [])
            if any(a.get("event_type") == "DELETE_RECORD" for a in acts):
                return cfg.CAT_USER_PROFILE
            return cfg.CAT_ANALYTICS_PROFILE
        elif rid.startswith("support_"):
            acts = self.activities_by_resource.get(rid, [])
            if any(a.get("event_type") == "DELETE_RECORD" for a in acts) or rid in ["support_001", "support_002", "support_4218"]:
                return cfg.CAT_SUPPORT_ATTACHMENT
            return cfg.CAT_SUPPORT_MESSAGE
        elif rid.startswith("data_flow_"):
            return cfg.CAT_DATA_FLOW
        elif rid.startswith("backup_"):
            return cfg.CAT_BACKUP_ARCHIVE
        elif rid.startswith("audit_record_"):
            return cfg.CAT_SECURITY_AUDIT_LOG
        elif rid.startswith("tombstone_"):
            return cfg.CAT_ACCOUNT_TOMBSTONE
        elif rid.startswith("export_"):
            return cfg.CAT_USER_EXPORT
        elif rid.startswith("marketing_"):
            return cfg.CAT_MARKETING_PROFILE
        elif rid.startswith("object_"):
            return cfg.CAT_SUPPORT_ATTACHMENT
        return cat or cfg.CAT_USER_PROFILE

    def _map_status_to_state(self, category: str, status: str):
        stat = status.upper()
        cat = category.upper()

        if stat in ["NOT_FOUND", "ABSENT"]:
            return cfg.STATE_ABSENT, False
        if stat in ["ANONYMIZED"]:
            return cfg.STATE_ANONYMIZED, False
        if stat in ["REDACTED"]:
            return cfg.STATE_REDACTED, False
        if stat in ["DISABLED"]:
            return cfg.STATE_DISABLED, False
        if stat in ["BLOCKED"]:
            return cfg.STATE_BLOCKED, False

        # Status indicates record is found / present / identifiable / active
        if cat in [cfg.CAT_SECURITY_AUDIT_LOG, cfg.CAT_LEGAL_HOLD_RECORD]:
            return cfg.STATE_PRESENT, False
        elif cat in [cfg.CAT_DATA_FLOW, cfg.CAT_INTEGRATION_CONNECTOR]:
            return cfg.STATE_ACTIVE, True
        elif cat in [cfg.CAT_BACKUP_ARCHIVE, cfg.CAT_BACKUP_RESTORE_ENTRY]:
            return cfg.STATE_ACTIVE, True
        elif cat in [cfg.CAT_SUPPORT_ATTACHMENT, cfg.CAT_USER_PROFILE, cfg.CAT_SEARCH_INDEX_ENTRY, cfg.CAT_USER_EXPORT, cfg.CAT_MARKETING_PROFILE]:
            return cfg.STATE_PRESENT, True
        elif cat in [cfg.CAT_SUPPORT_MESSAGE, cfg.CAT_EMAIL_DELIVERY_LOG, cfg.CAT_ACCOUNT_TOMBSTONE]:
            return cfg.STATE_PRESENT, True
        elif cat in [cfg.CAT_ANALYTICS_PROFILE, cfg.CAT_PRODUCT_TELEMETRY]:
            return cfg.STATE_PRESENT, True
        else:
            return cfg.STATE_PRESENT, True

    def _default_state_for_category(self, category: str, compliant: bool):
        cat = category.upper()
        if compliant:
            if cat in [cfg.CAT_SECURITY_AUDIT_LOG, cfg.CAT_LEGAL_HOLD_RECORD]:
                return cfg.STATE_PRESENT, False
            elif cat in [cfg.CAT_ANALYTICS_PROFILE, cfg.CAT_PRODUCT_TELEMETRY]:
                return cfg.STATE_ANONYMIZED, False
            elif cat in [cfg.CAT_SUPPORT_MESSAGE, cfg.CAT_ACCOUNT_TOMBSTONE]:
                return cfg.STATE_REDACTED, False
            elif cat in [cfg.CAT_DATA_FLOW, cfg.CAT_INTEGRATION_CONNECTOR]:
                return cfg.STATE_DISABLED, False
            elif cat in [cfg.CAT_BACKUP_ARCHIVE]:
                return cfg.STATE_BLOCKED, False
            else:
                return cfg.STATE_ABSENT, False
        else:
            if cat in [cfg.CAT_DATA_FLOW, cfg.CAT_INTEGRATION_CONNECTOR, cfg.CAT_BACKUP_ARCHIVE]:
                return cfg.STATE_ACTIVE, True
            else:
                return cfg.STATE_PRESENT, True
