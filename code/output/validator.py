"""Validates output.csv against all competition rules and schema constraints."""

import csv
import json
from pathlib import Path
from typing import List, Optional, Set, Tuple
import code.config as cfg

REQUIRED_STEP_FIELDS = {
    "step_no",
    "phase",
    "system_id",
    "resource_id",
    "operation",
    "state",
    "evidence_id",
}

PHASE_ALLOWED_OPS = {
    cfg.PHASE_FINDING: {
        cfg.OP_REPORT_REMAINING_RECORD,
        cfg.OP_REPORT_EXPOSED_PII,
        cfg.OP_REPORT_ACTIVE_DATA_FLOW,
        cfg.OP_REPORT_RESTORE_RISK,
    },
    cfg.PHASE_REMEDIATION: {
        cfg.OP_DISABLE_DATA_FLOW,
        cfg.OP_BLOCK_RESTORE,
        cfg.OP_DELETE_RECORD,
        cfg.OP_REDACT_RECORD,
        cfg.OP_ANONYMIZE_RECORD,
    },
    cfg.PHASE_VERIFICATION: {
        cfg.OP_VERIFY_RECORD_ABSENT,
        cfg.OP_VERIFY_RECORD_PRESENT,
        cfg.OP_VERIFY_RECORD_REDACTED,
        cfg.OP_VERIFY_RECORD_ANONYMIZED,
        cfg.OP_VERIFY_DATA_FLOW_DISABLED,
        cfg.OP_VERIFY_RESTORE_BLOCKED,
    },
}

class ValidationResult:
    def __init__(self):
        self.is_valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_error(self, err: str):
        self.is_valid = False
        self.errors.append(err)

    def add_warning(self, warn: str):
        self.warnings.append(warn)

class OutputValidator:
    """Rigorous validator ensuring generated predictions strictly adhere to challenge rules."""

    @staticmethod
    def validate_file(
        output_path: Path,
        expected_count: Optional[int] = None,
        valid_evidence_ids: Optional[Set[str]] = None,
    ) -> ValidationResult:
        res = ValidationResult()
        path = Path(output_path)

        if not path.exists():
            res.add_error(f"Output file does not exist: {path}")
            return res

        rows = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames != ["case_id", "deletion_status", "steps_json"]:
                    res.add_error(
                        f"Invalid CSV headers: {reader.fieldnames}. Expected: ['case_id', 'deletion_status', 'steps_json']"
                    )
                    return res
                for row in reader:
                    rows.append(row)
        except Exception as e:
            res.add_error(f"Failed to read CSV file: {e}")
            return res

        if expected_count is not None and len(rows) != expected_count:
            res.add_error(f"Row count mismatch: got {len(rows)}, expected {expected_count}")

        seen_case_ids = set()

        for idx, row in enumerate(rows, 1):
            cid = row.get("case_id", "").strip()
            status = row.get("deletion_status", "").strip()
            steps_str = row.get("steps_json", "").strip()

            if not cid:
                res.add_error(f"Row {idx}: Missing case_id")
                continue

            if cid in seen_case_ids:
                res.add_error(f"Row {idx}: Duplicate case_id: {cid}")
            seen_case_ids.add(cid)

            if status not in [cfg.STATUS_COMPLETE, cfg.STATUS_INCOMPLETE, cfg.STATUS_NOT_APPLICABLE]:
                res.add_error(f"Row {idx} ({cid}): Invalid status '{status}'")

            try:
                steps = json.loads(steps_str)
            except Exception as e:
                res.add_error(f"Row {idx} ({cid}): Malformed JSON in steps_json: {e}")
                continue

            if not isinstance(steps, list):
                res.add_error(f"Row {idx} ({cid}): steps_json must be a JSON list")
                continue

            # Validate each case's steps thoroughly
            step_errors = OutputValidator.validate_steps(cid, status, steps, valid_evidence_ids)
            for err in step_errors:
                res.add_error(f"Row {idx} ({cid}): {err}")

        return res

    @staticmethod
    def validate_steps(
        case_id: str,
        status: str,
        steps: List[dict],
        valid_evidence_ids: Optional[Set[str]] = None,
    ) -> List[str]:
        """Validate an individual case's steps against rules and schema constraints."""
        errors = []

        if status not in [cfg.STATUS_COMPLETE, cfg.STATUS_INCOMPLETE, cfg.STATUS_NOT_APPLICABLE]:
            errors.append(f"Invalid status '{status}'")

        if not isinstance(steps, list):
            errors.append("steps_json must be a JSON list")
            return errors

        # Case-specific restriction 1: NOT_APPLICABLE must have steps_json == []
        if status == cfg.STATUS_NOT_APPLICABLE:
            if len(steps) != 0:
                errors.append("NOT_APPLICABLE cases: steps_json must be empty []")
            return errors

        # Case-specific restriction 2: COMPLETE must only have VERIFICATION steps
        if status == cfg.STATUS_COMPLETE:
            non_verif = [s for s in steps if s.get("phase") != cfg.PHASE_VERIFICATION]
            if non_verif:
                errors.append(f"COMPLETE status cannot have FINDING or REMEDIATION steps: {non_verif}")

        # Case-specific restriction 3: INCOMPLETE should have findings, remediations, and verifications
        if status == cfg.STATUS_INCOMPLETE:
            phases_present = {s.get("phase") for s in steps}
            if cfg.PHASE_FINDING not in phases_present:
                errors.append("INCOMPLETE case must contain at least one FINDING step")
            if cfg.PHASE_REMEDIATION not in phases_present:
                errors.append("INCOMPLETE case must contain at least one REMEDIATION step")

        current_phase_num = 0
        prev_sort_key = None

        for s_idx, step in enumerate(steps, 1):
            if not isinstance(step, dict):
                errors.append(f"Step {s_idx}: step must be a JSON object, got {type(step)}")
                continue

            # Field presence check
            step_fields = set(step.keys())
            if step_fields != REQUIRED_STEP_FIELDS:
                missing = REQUIRED_STEP_FIELDS - step_fields
                extra = step_fields - REQUIRED_STEP_FIELDS
                if missing:
                    errors.append(f"Step {s_idx}: Missing required fields: {missing}")
                if extra:
                    errors.append(f"Step {s_idx}: Unexpected extra fields: {extra}")

            step_no = step.get("step_no")
            if step_no != s_idx:
                errors.append(f"Step {s_idx}: step_no is {step_no}, expected {s_idx}")

            phase = step.get("phase")
            if phase not in cfg.PHASE_ORDER_MAP:
                errors.append(f"Step {s_idx}: Invalid phase '{phase}'")
            else:
                p_num = cfg.PHASE_ORDER_MAP[phase]
                if p_num < current_phase_num:
                    errors.append(f"Step {s_idx}: Phase out of order ({phase} after higher phase)")
                current_phase_num = p_num

            op = step.get("operation")
            if op not in cfg.ALL_OPERATIONS:
                errors.append(f"Step {s_idx}: Invalid operation '{op}'")
            elif phase in PHASE_ALLOWED_OPS and op not in PHASE_ALLOWED_OPS[phase]:
                errors.append(f"Step {s_idx}: Operation '{op}' not allowed in phase '{phase}'")

            st = step.get("state")
            if st not in cfg.ALL_STATES:
                errors.append(f"Step {s_idx}: Invalid state '{st}'")
            elif op in cfg.OPERATION_STATE_MAPPING:
                expected_st = cfg.OPERATION_STATE_MAPPING[op]
                if st != expected_st:
                    errors.append(f"Step {s_idx}: Invalid state '{st}' for operation '{op}', expected '{expected_st}'")

            sys_id = step.get("system_id", "")
            if not sys_id or sys_id not in cfg.ALL_SYSTEMS:
                errors.append(f"Step {s_idx}: Invalid or unknown system_id '{sys_id}'")

            rid = step.get("resource_id", "")
            if not rid:
                errors.append(f"Step {s_idx}: Missing resource_id")

            # Evidence ID validation
            ev_id = step.get("evidence_id")
            if ev_id is None:
                errors.append(f"Step {s_idx}: evidence_id is null")
            elif status == cfg.STATUS_COMPLETE:
                if not ev_id:
                    errors.append(f"Step {s_idx}: COMPLETE steps must cite a valid evidence_id")
                elif valid_evidence_ids and ev_id not in valid_evidence_ids:
                    errors.append(f"Step {s_idx}: Unknown evidence_id '{ev_id}'")
            elif status == cfg.STATUS_INCOMPLETE:
                if phase == cfg.PHASE_FINDING:
                    if not ev_id:
                        errors.append(f"Step {s_idx}: FINDING steps must cite an evidence_id")
                    elif valid_evidence_ids and ev_id not in valid_evidence_ids:
                        errors.append(f"Step {s_idx}: Unknown evidence_id '{ev_id}'")
                else:
                    if ev_id != "":
                        errors.append(f"Step {s_idx}: {phase} step in INCOMPLETE case must have empty evidence_id, got '{ev_id}'")

            # Step ordering check: Phase -> Operation -> system_id -> resource_id
            p_order = cfg.PHASE_ORDER_MAP.get(phase, 99)
            op_order = cfg.OPERATION_ORDER_MAP.get(op, 99)
            sort_key = (p_order, op_order, str(sys_id), str(rid))
            if prev_sort_key is not None and sort_key < prev_sort_key:
                errors.append(f"Step {s_idx}: Step ordering violation ({sort_key} came after {prev_sort_key})")
            prev_sort_key = sort_key

        return errors
