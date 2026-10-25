"""Plans findings, remediations, and verification checks adhering to strict ordering rules."""

from typing import Any, Dict, List, Tuple
import code.config as cfg
from code.policy.policy_engine import PolicyEngine, PolicyEvaluationResult
from code.audit.state_reconstructor import ResourceState

class RemediationPlanner:
    """Constructs sorted, validated audit steps and determines overall deletion status."""

    def __init__(self, policy_engine: PolicyEngine):
        self.policy_engine = policy_engine

    def plan_steps(
        self, resource_states: List[ResourceState]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Generate ordered findings, remediation, and verification steps from resource states."""
        # Deduplicate resources by resource_id
        unique_resources = {}
        for r in resource_states:
            if r.resource_id not in unique_resources:
                unique_resources[r.resource_id] = r
            else:
                # If existing is compliant but this is violation, prefer violation
                if not unique_resources[r.resource_id].is_violation and r.is_violation:
                    unique_resources[r.resource_id] = r

        # Evaluate each resource under policy
        evaluated = []
        has_violations = False

        for rid, res in unique_resources.items():
            eval_res = self.policy_engine.evaluate_resource(res.category, res.state)
            is_violation = not eval_res.is_compliant or res.is_violation
            if is_violation:
                has_violations = True
            evaluated.append((res, eval_res, is_violation))

        deletion_status = cfg.STATUS_INCOMPLETE if has_violations else cfg.STATUS_COMPLETE

        raw_steps = []

        if has_violations:
            # INCOMPLETE deletion
            # 1. FINDING steps (with valid evidence_id where violation was observed)
            for res, eval_res, is_violation in evaluated:
                if is_violation and eval_res.finding_op:
                    raw_steps.append({
                        "phase": cfg.PHASE_FINDING,
                        "system_id": res.system_id,
                        "resource_id": res.resource_id,
                        "operation": eval_res.finding_op,
                        "state": eval_res.finding_state or cfg.STATE_PRESENT,
                        "evidence_id": res.evidence_id,
                    })

            # 2. REMEDIATION steps (evidence_id is empty string "")
            for res, eval_res, is_violation in evaluated:
                if is_violation and eval_res.remediation_op:
                    raw_steps.append({
                        "phase": cfg.PHASE_REMEDIATION,
                        "system_id": res.system_id,
                        "resource_id": res.resource_id,
                        "operation": eval_res.remediation_op,
                        "state": eval_res.remediation_state or cfg.STATE_ABSENT,
                        "evidence_id": "",
                    })

            # 3. VERIFICATION steps (for all resources; evidence_id is empty string "")
            for res, eval_res, is_violation in evaluated:
                if eval_res.verification_op:
                    raw_steps.append({
                        "phase": cfg.PHASE_VERIFICATION,
                        "system_id": res.system_id,
                        "resource_id": res.resource_id,
                        "operation": eval_res.verification_op,
                        "state": eval_res.verification_state or cfg.STATE_ABSENT,
                        "evidence_id": "",
                    })

        else:
            # COMPLETE deletion
            # ONLY VERIFICATION steps, all citing valid evidence proving compliance
            for res, eval_res, _ in evaluated:
                if eval_res.verification_op:
                    raw_steps.append({
                        "phase": cfg.PHASE_VERIFICATION,
                        "system_id": res.system_id,
                        "resource_id": res.resource_id,
                        "operation": eval_res.verification_op,
                        "state": eval_res.verification_state or cfg.STATE_ABSENT,
                        "evidence_id": res.evidence_id,
                    })

        # Sort steps according to the official sorting contract:
        # Phase order -> Operation order -> system_id ASC -> resource_id ASC
        def sort_key(s: Dict[str, Any]):
            p_order = cfg.PHASE_ORDER_MAP.get(s["phase"], 99)
            op_order = cfg.OPERATION_ORDER_MAP.get(s["operation"], 99)
            return (p_order, op_order, s["system_id"], s["resource_id"])

        raw_steps.sort(key=sort_key)

        # Number steps sequentially starting at 1
        final_steps = []
        for i, s in enumerate(raw_steps, 1):
            step = {
                "step_no": i,
                "phase": s["phase"],
                "system_id": s["system_id"],
                "resource_id": s["resource_id"],
                "operation": s["operation"],
                "state": s["state"],
                "evidence_id": s["evidence_id"],
            }
            final_steps.append(step)

        return deletion_status, final_steps
