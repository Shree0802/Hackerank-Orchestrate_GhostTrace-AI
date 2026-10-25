"""Unit tests for the official sorting contract and phase/operation ordering."""

import unittest
import pandas as pd
from code.policy.rules_loader import PolicyRulesLoader
from code.policy.policy_engine import PolicyEngine
from code.agent.remediation_planner import RemediationPlanner
from code.audit.state_reconstructor import ResourceState
import code.config as cfg

class TestOrderingContract(unittest.TestCase):
    def setUp(self):
        rules_data = [
            {"rule_id": "rule_01", "data_category": "USER_PROFILE", "condition": "Always", "required_action": "DELETE"},
            {"rule_id": "rule_03", "data_category": "SEARCH_INDEX_ENTRY", "condition": "Always", "required_action": "DELETE"},
            {"rule_id": "rule_07", "data_category": "ANALYTICS_PROFILE", "condition": "Attributable", "required_action": "ANONYMIZE"},
            {"rule_id": "rule_14", "data_category": "BACKUP_ARCHIVE", "condition": "Restore access", "required_action": "RETAIN"},
            {"rule_id": "rule_12", "data_category": "SECURITY_AUDIT_LOG", "condition": "Retention period", "required_action": "RETAIN"},
        ]
        df_rules = pd.DataFrame(rules_data)
        loader = PolicyRulesLoader(df_rules)
        self.engine = PolicyEngine(loader)
        self.planner = RemediationPlanner(self.engine)

    def test_phase_and_operation_sorting(self):
        # A mix of violations across search, analytics, backup, and compliant account & audit
        states = [
            ResourceState(resource_id="account_001", system_id="account_service", category="USER_PROFILE", state="ABSENT", evidence_id="", is_violation=False),
            ResourceState(resource_id="backup_100", system_id="backup_service", category="BACKUP_ARCHIVE", state="ACTIVE", evidence_id="ev_01", is_violation=True),
            ResourceState(resource_id="analytics_200", system_id="analytics_platform", category="ANALYTICS_PROFILE", state="PRESENT", evidence_id="ev_02", is_violation=True),
            ResourceState(resource_id="search_300", system_id="search_service", category="SEARCH_INDEX_ENTRY", state="PRESENT", evidence_id="ev_03", is_violation=True),
            ResourceState(resource_id="audit_record_400", system_id="security_service", category="SECURITY_AUDIT_LOG", state="PRESENT", evidence_id="", is_violation=False),
        ]

        status, steps = self.planner.plan_steps(states)
        self.assertEqual(status, cfg.STATUS_INCOMPLETE)

        # 1. Assert phases are strictly ordered: FINDING -> REMEDIATION -> VERIFICATION
        phases = [s["phase"] for s in steps]
        finding_indices = [i for i, p in enumerate(phases) if p == cfg.PHASE_FINDING]
        rem_indices = [i for i, p in enumerate(phases) if p == cfg.PHASE_REMEDIATION]
        ver_indices = [i for i, p in enumerate(phases) if p == cfg.PHASE_VERIFICATION]

        self.assertTrue(max(finding_indices) < min(rem_indices))
        self.assertTrue(max(rem_indices) < min(ver_indices))

        # 2. Assert FINDINGS ordered: REPORT_REMAINING_RECORD -> REPORT_EXPOSED_PII -> REPORT_RESTORE_RISK
        findings = [s for s in steps if s["phase"] == cfg.PHASE_FINDING]
        finding_ops = [s["operation"] for s in findings]
        self.assertEqual(
            finding_ops,
            [cfg.OP_REPORT_REMAINING_RECORD, cfg.OP_REPORT_EXPOSED_PII, cfg.OP_REPORT_RESTORE_RISK]
        )

        # 3. Assert REMEDIATIONS ordered: BLOCK_RESTORE -> DELETE_RECORD -> ANONYMIZE_RECORD
        rems = [s for s in steps if s["phase"] == cfg.PHASE_REMEDIATION]
        rem_ops = [s["operation"] for s in rems]
        self.assertEqual(
            rem_ops,
            [cfg.OP_BLOCK_RESTORE, cfg.OP_DELETE_RECORD, cfg.OP_ANONYMIZE_RECORD]
        )

        # 4. Assert step numbers are sequential starting from 1
        step_nos = [s["step_no"] for s in steps]
        self.assertEqual(step_nos, list(range(1, len(steps) + 1)))

if __name__ == "__main__":
    unittest.main()
