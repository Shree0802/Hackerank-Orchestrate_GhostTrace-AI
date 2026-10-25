"""Custom synthetic evaluation cases covering diverse edge cases and scenarios."""

from typing import Any, Dict, List

CUSTOM_EVALUATION_CASES: List[Dict[str, Any]] = [
    {
        "case_id": "synth_01_non_deletion_export",
        "description": "Customer asks for a data export copy of their profile data, not deletion.",
        "request": {
            "case_id": "synth_01_non_deletion_export",
            "email": "synthetic.export.user@example.com",
            "subject": "Data Export Request",
            "request_text": "Please send me a full copy of all personal data held about my account under GDPR Article 15.",
            "requested_at": "2026-08-01T10:00:00Z",
            "reported_at": "2026-08-02T10:00:00Z",
            "audit_at": "2026-08-10T10:00:00Z",
        },
        "expected_status": "NOT_APPLICABLE",
        "expected_steps": [],
    },
    {
        "case_id": "synth_02_replica_restore_risk",
        "description": "Backup archive remains restorable despite profile deletion request.",
        "request": {
            "case_id": "synth_02_replica_restore_risk",
            "email": "synthetic.backup.user@example.com",
            "subject": "Delete my account permanently",
            "request_text": "I demand the complete erasure of my personal profile and all backups.",
            "requested_at": "2026-08-05T12:00:00Z",
            "reported_at": "2026-08-06T12:00:00Z",
            "audit_at": "2026-08-15T12:00:00Z",
        },
        "expected_status": "INCOMPLETE",
        "expected_steps": [
            {
                "step_no": 1,
                "phase": "FINDING",
                "system_id": "backup_service",
                "resource_id": "backup_synth_01",
                "operation": "REPORT_RESTORE_RISK",
                "state": "ACTIVE",
                "evidence_id": "evidence_32",
            },
            {
                "step_no": 2,
                "phase": "REMEDIATION",
                "system_id": "backup_service",
                "resource_id": "backup_synth_01",
                "operation": "BLOCK_RESTORE",
                "state": "BLOCKED",
                "evidence_id": "",
            },
            {
                "step_no": 3,
                "phase": "VERIFICATION",
                "system_id": "account_service",
                "resource_id": "account_synth_01",
                "operation": "VERIFY_RECORD_ABSENT",
                "state": "ABSENT",
                "evidence_id": "",
            },
            {
                "step_no": 4,
                "phase": "VERIFICATION",
                "system_id": "backup_service",
                "resource_id": "backup_synth_01",
                "operation": "VERIFY_RESTORE_BLOCKED",
                "state": "BLOCKED",
                "evidence_id": "",
            },
        ],
    },
    {
        "case_id": "synth_03_active_data_flow",
        "description": "Integration connector remains enabled, risking downstream reinjection.",
        "request": {
            "case_id": "synth_03_active_data_flow",
            "email": "synthetic.connector.user@example.com",
            "subject": "Please erase all my data",
            "request_text": "Please delete all records and disconnect any continuous sync feeds.",
            "requested_at": "2026-08-10T08:00:00Z",
            "reported_at": "2026-08-11T08:00:00Z",
            "audit_at": "2026-08-20T08:00:00Z",
        },
        "expected_status": "INCOMPLETE",
        "expected_steps": [
            {
                "step_no": 1,
                "phase": "FINDING",
                "system_id": "integration_service",
                "resource_id": "data_flow_synth_01",
                "operation": "REPORT_ACTIVE_DATA_FLOW",
                "state": "ACTIVE",
                "evidence_id": "evidence_14",
            },
            {
                "step_no": 2,
                "phase": "REMEDIATION",
                "system_id": "integration_service",
                "resource_id": "data_flow_synth_01",
                "operation": "DISABLE_DATA_FLOW",
                "state": "DISABLED",
                "evidence_id": "",
            },
            {
                "step_no": 3,
                "phase": "VERIFICATION",
                "system_id": "account_service",
                "resource_id": "account_synth_02",
                "operation": "VERIFY_RECORD_ABSENT",
                "state": "ABSENT",
                "evidence_id": "",
            },
            {
                "step_no": 4,
                "phase": "VERIFICATION",
                "system_id": "integration_service",
                "resource_id": "data_flow_synth_01",
                "operation": "VERIFY_DATA_FLOW_DISABLED",
                "state": "DISABLED",
                "evidence_id": "",
            },
        ],
    },
    {
        "case_id": "synth_04_exposed_tombstone_pii",
        "description": "Account tombstone retains plaintext email address instead of redaction.",
        "request": {
            "case_id": "synth_04_exposed_tombstone_pii",
            "email": "synthetic.tombstone.user@example.com",
            "subject": "Erasure request",
            "request_text": "Forget me completely from all account databases.",
            "requested_at": "2026-08-12T14:00:00Z",
            "reported_at": "2026-08-13T14:00:00Z",
            "audit_at": "2026-08-22T14:00:00Z",
        },
        "expected_status": "INCOMPLETE",
        "expected_steps": [
            {
                "step_no": 1,
                "phase": "FINDING",
                "system_id": "identity_service",
                "resource_id": "tombstone_synth_01",
                "operation": "REPORT_EXPOSED_PII",
                "state": "PRESENT",
                "evidence_id": "evidence_42",
            },
            {
                "step_no": 2,
                "phase": "REMEDIATION",
                "system_id": "identity_service",
                "resource_id": "tombstone_synth_01",
                "operation": "REDACT_RECORD",
                "state": "REDACTED",
                "evidence_id": "",
            },
            {
                "step_no": 3,
                "phase": "VERIFICATION",
                "system_id": "account_service",
                "resource_id": "account_synth_03",
                "operation": "VERIFY_RECORD_ABSENT",
                "state": "ABSENT",
                "evidence_id": "",
            },
            {
                "step_no": 4,
                "phase": "VERIFICATION",
                "system_id": "identity_service",
                "resource_id": "tombstone_synth_01",
                "operation": "VERIFY_RECORD_REDACTED",
                "state": "REDACTED",
                "evidence_id": "",
            },
        ],
    },
    {
        "case_id": "synth_05_retained_security_audit",
        "description": "Legitimate audit record correctly retained under compliance policy.",
        "request": {
            "case_id": "synth_05_retained_security_audit",
            "email": "synthetic.audit.user@example.com",
            "subject": "Delete my profile",
            "request_text": "Please delete my account and personal data.",
            "requested_at": "2026-08-15T09:00:00Z",
            "reported_at": "2026-08-16T09:00:00Z",
            "audit_at": "2026-08-25T09:00:00Z",
        },
        "expected_status": "COMPLETE",
        "expected_steps": [
            {
                "step_no": 1,
                "phase": "VERIFICATION",
                "system_id": "account_service",
                "resource_id": "account_synth_04",
                "operation": "VERIFY_RECORD_ABSENT",
                "state": "ABSENT",
                "evidence_id": "evidence_54",
            },
            {
                "step_no": 2,
                "phase": "VERIFICATION",
                "system_id": "security_service",
                "resource_id": "audit_record_synth_01",
                "operation": "VERIFY_RECORD_PRESENT",
                "state": "PRESENT",
                "evidence_id": "evidence_37",
            },
        ],
    },
    {
        "case_id": "synth_06_fully_compliant_multi_system",
        "description": "Deletion verified across account, analytics (anonymized), and security audit.",
        "request": {
            "case_id": "synth_06_fully_compliant_multi_system",
            "email": "synthetic.compliant.user@example.com",
            "subject": "GDPR deletion request",
            "request_text": "Kindly erase all my customer information.",
            "requested_at": "2026-08-18T11:00:00Z",
            "reported_at": "2026-08-19T11:00:00Z",
            "audit_at": "2026-08-28T11:00:00Z",
        },
        "expected_status": "COMPLETE",
        "expected_steps": [
            {
                "step_no": 1,
                "phase": "VERIFICATION",
                "system_id": "account_service",
                "resource_id": "account_synth_05",
                "operation": "VERIFY_RECORD_ABSENT",
                "state": "ABSENT",
                "evidence_id": "evidence_94",
            },
            {
                "step_no": 2,
                "phase": "VERIFICATION",
                "system_id": "security_service",
                "resource_id": "audit_record_synth_02",
                "operation": "VERIFY_RECORD_PRESENT",
                "state": "PRESENT",
                "evidence_id": "evidence_94",
            },
            {
                "step_no": 3,
                "phase": "VERIFICATION",
                "system_id": "analytics_platform",
                "resource_id": "analytics_synth_01",
                "operation": "VERIFY_RECORD_ANONYMIZED",
                "state": "ANONYMIZED",
                "evidence_id": "evidence_94",
            },
        ],
    },
]

def run_custom_evaluations() -> List[Dict[str, Any]]:
    """Runs evaluations against synthetic benchmark cases covering all scenario archetypes."""
    from code.agent.request_classifier import RequestClassifier
    from code.policy.policy_engine import PolicyEngine
    from code.policy.rules_loader import PolicyRulesLoader
    from code.agent.remediation_planner import RemediationPlanner
    from code.audit.state_reconstructor import ResourceState
    from pathlib import Path
    from code.ingestion.csv_loader import CSVDataLoader
    import code.config as cfg

    loader = CSVDataLoader(Path("dataset"))
    df_rules = loader.load_deletion_rules()
    policy_engine = PolicyEngine(PolicyRulesLoader(df_rules))
    planner = RemediationPlanner(policy_engine)

    results = []
    for case in CUSTOM_EVALUATION_CASES:
        cid = case["case_id"]
        req = case["request"]
        expected_status = case["expected_status"]
        expected_steps = case["expected_steps"]

        # 1. Classification check
        is_del = RequestClassifier.is_deletion_request(req.get("request_text", ""), req.get("subject", ""))
        
        if not is_del:
            pred_status = cfg.STATUS_NOT_APPLICABLE
            pred_steps = []
        else:
            # Build mock resource states from expected steps to verify planner & policy contracts
            mock_states = []
            finding_rids = set()
            for s in expected_steps:
                if s["phase"] == "FINDING":
                    finding_rids.add(s["resource_id"])
                    cat = cfg.CAT_BACKUP_ARCHIVE if "backup" in s["resource_id"] else (
                        cfg.CAT_DATA_FLOW if "data_flow" in s["resource_id"] else (
                            cfg.CAT_ACCOUNT_TOMBSTONE if "tombstone" in s["resource_id"] else cfg.CAT_USER_PROFILE
                        )
                    )
                    mock_states.append(
                        ResourceState(
                            resource_id=s["resource_id"],
                            system_id=s["system_id"],
                            category=cat,
                            state=s["state"],
                            evidence_id=s.get("evidence_id", ""),
                            captured_at=req["audit_at"],
                            is_violation=True,
                        )
                    )

            for s in expected_steps:
                if s["phase"] == "VERIFICATION" and s["resource_id"] not in finding_rids:
                    cat = cfg.CAT_USER_PROFILE if "account" in s["resource_id"] else (
                        cfg.CAT_ANALYTICS_PROFILE if "analytics" in s["resource_id"] else (
                            cfg.CAT_SECURITY_AUDIT_LOG if "audit_record" in s["resource_id"] else cfg.CAT_USER_PROFILE
                        )
                    )
                    mock_states.append(
                        ResourceState(
                            resource_id=s["resource_id"],
                            system_id=s["system_id"],
                            category=cat,
                            state=s["state"],
                            evidence_id=s.get("evidence_id", ""),
                            captured_at=req["audit_at"],
                            is_violation=False,
                        )
                    )

            pred_status, pred_steps = planner.plan_steps(mock_states)

        status_match = (pred_status == expected_status)
        step_count_match = (len(pred_steps) == len(expected_steps))
        passed = status_match and step_count_match

        results.append({
            "case_id": cid,
            "description": case["description"],
            "expected_status": expected_status,
            "pred_status": pred_status,
            "expected_steps_count": len(expected_steps),
            "pred_steps_count": len(pred_steps),
            "passed": passed,
        })
        print(f"  [{'PASS' if passed else 'FAIL'}] {cid}: expected={expected_status} pred={pred_status} ({len(pred_steps)}/{len(expected_steps)} steps)")

    return results
