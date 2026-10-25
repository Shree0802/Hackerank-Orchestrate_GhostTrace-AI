"""Unit tests for the policy evaluation engine."""

import unittest
import pandas as pd
from code.policy.rules_loader import PolicyRulesLoader
from code.policy.policy_engine import PolicyEngine
import code.config as cfg

class TestPolicyEngine(unittest.TestCase):
    def setUp(self):
        rules_data = [
            {"rule_id": "rule_01", "data_category": "USER_PROFILE", "condition": "Always", "required_action": "DELETE"},
            {"rule_id": "rule_03", "data_category": "SEARCH_INDEX_ENTRY", "condition": "Always", "required_action": "DELETE"},
            {"rule_id": "rule_05", "data_category": "SUPPORT_MESSAGE", "condition": "Conversation context", "required_action": "REDACT"},
            {"rule_id": "rule_06", "data_category": "SUPPORT_ATTACHMENT", "condition": "Subject attachment", "required_action": "DELETE"},
            {"rule_id": "rule_07", "data_category": "ANALYTICS_PROFILE", "condition": "Attributable", "required_action": "ANONYMIZE"},
            {"rule_id": "rule_12", "data_category": "SECURITY_AUDIT_LOG", "condition": "Retention period", "required_action": "RETAIN"},
            {"rule_id": "rule_14", "data_category": "BACKUP_ARCHIVE", "condition": "Restore access", "required_action": "RETAIN"},
            {"rule_id": "rule_15", "data_category": "ACCOUNT_TOMBSTONE", "condition": "Deleted account", "required_action": "REDACT"},
        ]
        df_rules = pd.DataFrame(rules_data)
        loader = PolicyRulesLoader(df_rules)
        self.engine = PolicyEngine(loader)

    def test_user_profile_compliant(self):
        res = self.engine.evaluate_resource(cfg.CAT_USER_PROFILE, cfg.STATE_ABSENT)
        self.assertTrue(res.is_compliant)
        self.assertEqual(res.required_state, cfg.STATE_ABSENT)
        self.assertEqual(res.verification_op, cfg.OP_VERIFY_RECORD_ABSENT)

    def test_user_profile_violation(self):
        res = self.engine.evaluate_resource(cfg.CAT_USER_PROFILE, cfg.STATE_PRESENT)
        self.assertFalse(res.is_compliant)
        self.assertEqual(res.finding_op, cfg.OP_REPORT_REMAINING_RECORD)
        self.assertEqual(res.remediation_op, cfg.OP_DELETE_RECORD)
        self.assertEqual(res.verification_op, cfg.OP_VERIFY_RECORD_ABSENT)

    def test_analytics_profile_violation(self):
        res = self.engine.evaluate_resource(cfg.CAT_ANALYTICS_PROFILE, cfg.STATE_PRESENT)
        self.assertFalse(res.is_compliant)
        self.assertEqual(res.finding_op, cfg.OP_REPORT_EXPOSED_PII)
        self.assertEqual(res.remediation_op, cfg.OP_ANONYMIZE_RECORD)
        self.assertEqual(res.verification_op, cfg.OP_VERIFY_RECORD_ANONYMIZED)

    def test_data_flow_active_violation(self):
        res = self.engine.evaluate_resource(cfg.CAT_DATA_FLOW, cfg.STATE_ACTIVE)
        self.assertFalse(res.is_compliant)
        self.assertEqual(res.finding_op, cfg.OP_REPORT_ACTIVE_DATA_FLOW)
        self.assertEqual(res.remediation_op, cfg.OP_DISABLE_DATA_FLOW)
        self.assertEqual(res.verification_op, cfg.OP_VERIFY_DATA_FLOW_DISABLED)

    def test_backup_restore_active_violation(self):
        res = self.engine.evaluate_resource(cfg.CAT_BACKUP_ARCHIVE, cfg.STATE_ACTIVE)
        self.assertFalse(res.is_compliant)
        self.assertEqual(res.finding_op, cfg.OP_REPORT_RESTORE_RISK)
        self.assertEqual(res.remediation_op, cfg.OP_BLOCK_RESTORE)
        self.assertEqual(res.verification_op, cfg.OP_VERIFY_RESTORE_BLOCKED)

    def test_security_audit_log_retained(self):
        res = self.engine.evaluate_resource(cfg.CAT_SECURITY_AUDIT_LOG, cfg.STATE_PRESENT)
        self.assertTrue(res.is_compliant)
        self.assertEqual(res.verification_op, cfg.OP_VERIFY_RECORD_PRESENT)

if __name__ == "__main__":
    unittest.main()
