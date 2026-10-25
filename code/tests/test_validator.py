"""Unit tests for OutputValidator compliance checks."""

import unittest
from code.output.validator import OutputValidator
import code.config as cfg

class TestOutputValidator(unittest.TestCase):
    def test_valid_complete_steps(self):
        steps = [
            {
                "step_no": 1,
                "phase": cfg.PHASE_VERIFICATION,
                "system_id": "account_service",
                "resource_id": "account_001",
                "operation": cfg.OP_VERIFY_RECORD_ABSENT,
                "state": cfg.STATE_ABSENT,
                "evidence_id": "evidence_54",
            }
        ]
        errors = OutputValidator.validate_steps("case_01", cfg.STATUS_COMPLETE, steps)
        self.assertEqual(len(errors), 0)

    def test_complete_with_finding_fails(self):
        steps = [
            {
                "step_no": 1,
                "phase": cfg.PHASE_FINDING,
                "system_id": "account_service",
                "resource_id": "account_001",
                "operation": cfg.OP_REPORT_REMAINING_RECORD,
                "state": cfg.STATE_PRESENT,
                "evidence_id": "evidence_54",
            }
        ]
        errors = OutputValidator.validate_steps("case_01", cfg.STATUS_COMPLETE, steps)
        self.assertTrue(any("COMPLETE status cannot have FINDING" in e for e in errors))

    def test_incomplete_finding_without_evidence_fails(self):
        steps = [
            {
                "step_no": 1,
                "phase": cfg.PHASE_FINDING,
                "system_id": "account_service",
                "resource_id": "account_001",
                "operation": cfg.OP_REPORT_REMAINING_RECORD,
                "state": cfg.STATE_PRESENT,
                "evidence_id": "",
            }
        ]
        errors = OutputValidator.validate_steps("case_02", cfg.STATUS_INCOMPLETE, steps)
        self.assertTrue(any("must cite an evidence_id" in e for e in errors))

    def test_incomplete_remediation_with_evidence_fails(self):
        steps = [
            {
                "step_no": 1,
                "phase": cfg.PHASE_FINDING,
                "system_id": "account_service",
                "resource_id": "account_001",
                "operation": cfg.OP_REPORT_REMAINING_RECORD,
                "state": cfg.STATE_PRESENT,
                "evidence_id": "evidence_01",
            },
            {
                "step_no": 2,
                "phase": cfg.PHASE_REMEDIATION,
                "system_id": "account_service",
                "resource_id": "account_001",
                "operation": cfg.OP_DELETE_RECORD,
                "state": cfg.STATE_ABSENT,
                "evidence_id": "evidence_01",  # Invalid: must be empty
            }
        ]
        errors = OutputValidator.validate_steps("case_02", cfg.STATUS_INCOMPLETE, steps)
        self.assertTrue(any("must have empty evidence_id" in e for e in errors))

    def test_not_applicable_non_empty_steps_fails(self):
        steps = [
            {
                "step_no": 1,
                "phase": cfg.PHASE_VERIFICATION,
                "system_id": "account_service",
                "resource_id": "account_001",
                "operation": cfg.OP_VERIFY_RECORD_ABSENT,
                "state": cfg.STATE_ABSENT,
                "evidence_id": "",
            }
        ]
        errors = OutputValidator.validate_steps("case_03", cfg.STATUS_NOT_APPLICABLE, steps)
        self.assertTrue(any("steps_json must be empty" in e for e in errors))

    def test_invalid_operation_state_combination_fails(self):
        steps = [
            {
                "step_no": 1,
                "phase": cfg.PHASE_VERIFICATION,
                "system_id": "account_service",
                "resource_id": "account_001",
                "operation": cfg.OP_VERIFY_RECORD_ABSENT,
                "state": cfg.STATE_PRESENT,  # Invalid: expected ABSENT
                "evidence_id": "evidence_54",
            }
        ]
        errors = OutputValidator.validate_steps("case_01", cfg.STATUS_COMPLETE, steps)
        self.assertTrue(any("Invalid state 'PRESENT' for operation" in e for e in errors))

    def test_operation_phase_mismatch_fails(self):
        steps = [
            {
                "step_no": 1,
                "phase": cfg.PHASE_FINDING,
                "system_id": "account_service",
                "resource_id": "account_001",
                "operation": cfg.OP_DELETE_RECORD,  # Invalid for FINDING
                "state": cfg.STATE_ABSENT,
                "evidence_id": "evidence_54",
            }
        ]
        errors = OutputValidator.validate_steps("case_01", cfg.STATUS_INCOMPLETE, steps)
        self.assertTrue(any("not allowed in phase 'FINDING'" in e for e in errors))

    def test_step_ordering_violation_fails(self):
        steps = [
            {
                "step_no": 1,
                "phase": cfg.PHASE_VERIFICATION,
                "system_id": "search_service",
                "resource_id": "search_002",
                "operation": cfg.OP_VERIFY_RECORD_ABSENT,
                "state": cfg.STATE_ABSENT,
                "evidence_id": "evidence_54",
            },
            {
                "step_no": 2,
                "phase": cfg.PHASE_VERIFICATION,
                "system_id": "account_service",  # Invalid order: account_service should precede search_service
                "resource_id": "account_001",
                "operation": cfg.OP_VERIFY_RECORD_ABSENT,
                "state": cfg.STATE_ABSENT,
                "evidence_id": "evidence_54",
            }
        ]
        errors = OutputValidator.validate_steps("case_01", cfg.STATUS_COMPLETE, steps)
        self.assertTrue(any("Step ordering violation" in e for e in errors))

if __name__ == "__main__":
    unittest.main()
