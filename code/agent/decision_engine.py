"""High-level decision engine coordinating identity, state reconstruction, policy, and planning."""

from typing import Any, Dict, List, Tuple
import pandas as pd

from code.identity.resolver import IdentityResolver
from code.audit.state_reconstructor import StateReconstructor
from code.agent.remediation_planner import RemediationPlanner
from code.agent.request_classifier import RequestClassifier
import code.config as cfg

class DeletionDecisionEngine:
    """End-to-end decision engine for auditing customer deletion requests."""

    def __init__(
        self,
        resolver: IdentityResolver,
        reconstructor: StateReconstructor,
        planner: RemediationPlanner,
    ):
        self.resolver = resolver
        self.reconstructor = reconstructor
        self.planner = planner

    def process_request(self, request_row: pd.Series) -> Tuple[str, str, List[Dict[str, Any]]]:
        """Process a single deletion request and return (case_id, deletion_status, steps)."""
        case_id = str(request_row.get("case_id", "")).strip()
        email = str(request_row.get("email", "")).strip()
        req_text = str(request_row.get("request_text", ""))
        subject = str(request_row.get("subject", ""))
        t_req = str(request_row.get("requested_at", ""))
        t_rep = str(request_row.get("reported_at", ""))
        t_aud = str(request_row.get("audit_at", ""))
        rep_status = str(request_row.get("reported_status", "")).strip()

        # 1. Determine if request authorizes deletion
        if not RequestClassifier.is_deletion_request(req_text, subject):
            return case_id, cfg.STATUS_NOT_APPLICABLE, []

        # 2. Resolve identity across current and historical identifiers
        user = self.resolver.resolve_email(email)
        if not user:
            # Unresolvable user identity
            return case_id, cfg.STATUS_NOT_APPLICABLE, []

        # 3. Reconstruct true resource state at audit timestamp
        resource_states = self.reconstructor.reconstruct_for_request(
            case_id=case_id,
            user=user,
            requested_at=t_req,
            reported_at=t_rep,
            audit_at=t_aud,
            reported_status=rep_status,
        )

        # 4. Plan ordered findings, remediations, and verification steps
        status, steps = self.planner.plan_steps(resource_states)

        return case_id, status, steps
