"""Policy evaluation engine determining required treatments and compliance states."""

from dataclasses import dataclass
from typing import Optional, Tuple
from code.policy.rules_loader import PolicyRulesLoader
import code.config as cfg

@dataclass
class PolicyEvaluationResult:
    is_compliant: bool
    required_state: str
    finding_op: Optional[str] = None
    finding_state: Optional[str] = None
    remediation_op: Optional[str] = None
    remediation_state: Optional[str] = None
    verification_op: Optional[str] = None
    verification_state: Optional[str] = None

class PolicyEngine:
    """Evaluates resource observations against organizational deletion policies."""

    def __init__(self, rules_loader: PolicyRulesLoader):
        self.rules_loader = rules_loader

    def evaluate_resource(
        self, category: str, current_state: str
    ) -> PolicyEvaluationResult:
        """Evaluate a resource state against the required deletion policy."""
        cat_upper = category.upper()
        state_upper = current_state.upper()

        # 1. DELETE categories (USER_PROFILE, SEARCH_INDEX_ENTRY, USER_EXPORT, etc.)
        if cat_upper in [
            "USER_PROFILE", "SECONDARY_IDENTIFIER", "SEARCH_INDEX_ENTRY",
            "CACHE_ENTRY", "SUPPORT_ATTACHMENT", "USER_EXPORT", "MARKETING_PROFILE"
        ]:
            if state_upper == cfg.STATE_ABSENT:
                return PolicyEvaluationResult(
                    is_compliant=True,
                    required_state=cfg.STATE_ABSENT,
                    verification_op=cfg.OP_VERIFY_RECORD_ABSENT,
                    verification_state=cfg.STATE_ABSENT
                )
            else:
                return PolicyEvaluationResult(
                    is_compliant=False,
                    required_state=cfg.STATE_ABSENT,
                    finding_op=cfg.OP_REPORT_REMAINING_RECORD,
                    finding_state=cfg.STATE_PRESENT,
                    remediation_op=cfg.OP_DELETE_RECORD,
                    remediation_state=cfg.STATE_ABSENT,
                    verification_op=cfg.OP_VERIFY_RECORD_ABSENT,
                    verification_state=cfg.STATE_ABSENT
                )

        # 2. REDACT categories (SUPPORT_MESSAGE, EMAIL_DELIVERY_LOG, ACCOUNT_TOMBSTONE)
        elif cat_upper in ["SUPPORT_MESSAGE", "EMAIL_DELIVERY_LOG", "ACCOUNT_TOMBSTONE"]:
            if state_upper == cfg.STATE_REDACTED:
                return PolicyEvaluationResult(
                    is_compliant=True,
                    required_state=cfg.STATE_REDACTED,
                    verification_op=cfg.OP_VERIFY_RECORD_REDACTED,
                    verification_state=cfg.STATE_REDACTED
                )
            else:
                return PolicyEvaluationResult(
                    is_compliant=False,
                    required_state=cfg.STATE_REDACTED,
                    finding_op=cfg.OP_REPORT_EXPOSED_PII,
                    finding_state=cfg.STATE_PRESENT,
                    remediation_op=cfg.OP_REDACT_RECORD,
                    remediation_state=cfg.STATE_REDACTED,
                    verification_op=cfg.OP_VERIFY_RECORD_REDACTED,
                    verification_state=cfg.STATE_REDACTED
                )

        # 3. ANONYMIZE categories (ANALYTICS_PROFILE, PRODUCT_TELEMETRY)
        elif cat_upper in ["ANALYTICS_PROFILE", "PRODUCT_TELEMETRY"]:
            if state_upper == cfg.STATE_ANONYMIZED:
                return PolicyEvaluationResult(
                    is_compliant=True,
                    required_state=cfg.STATE_ANONYMIZED,
                    verification_op=cfg.OP_VERIFY_RECORD_ANONYMIZED,
                    verification_state=cfg.STATE_ANONYMIZED
                )
            else:
                return PolicyEvaluationResult(
                    is_compliant=False,
                    required_state=cfg.STATE_ANONYMIZED,
                    finding_op=cfg.OP_REPORT_EXPOSED_PII,
                    finding_state=cfg.STATE_PRESENT,
                    remediation_op=cfg.OP_ANONYMIZE_RECORD,
                    remediation_state=cfg.STATE_ANONYMIZED,
                    verification_op=cfg.OP_VERIFY_RECORD_ANONYMIZED,
                    verification_state=cfg.STATE_ANONYMIZED
                )

        # 4. DATA_FLOW categories (integration sync/connectors)
        elif cat_upper in ["DATA_FLOW", "INTEGRATION_CONNECTOR"]:
            if state_upper == cfg.STATE_DISABLED:
                return PolicyEvaluationResult(
                    is_compliant=True,
                    required_state=cfg.STATE_DISABLED,
                    verification_op=cfg.OP_VERIFY_DATA_FLOW_DISABLED,
                    verification_state=cfg.STATE_DISABLED
                )
            else:
                return PolicyEvaluationResult(
                    is_compliant=False,
                    required_state=cfg.STATE_DISABLED,
                    finding_op=cfg.OP_REPORT_ACTIVE_DATA_FLOW,
                    finding_state=cfg.STATE_ACTIVE,
                    remediation_op=cfg.OP_DISABLE_DATA_FLOW,
                    remediation_state=cfg.STATE_DISABLED,
                    verification_op=cfg.OP_VERIFY_DATA_FLOW_DISABLED,
                    verification_state=cfg.STATE_DISABLED
                )

        # 5. BACKUP_ARCHIVE (restore access)
        elif cat_upper in ["BACKUP_ARCHIVE", "BACKUP_RESTORE_ENTRY"]:
            if state_upper == cfg.STATE_BLOCKED:
                return PolicyEvaluationResult(
                    is_compliant=True,
                    required_state=cfg.STATE_BLOCKED,
                    verification_op=cfg.OP_VERIFY_RESTORE_BLOCKED,
                    verification_state=cfg.STATE_BLOCKED
                )
            else:
                return PolicyEvaluationResult(
                    is_compliant=False,
                    required_state=cfg.STATE_BLOCKED,
                    finding_op=cfg.OP_REPORT_RESTORE_RISK,
                    finding_state=cfg.STATE_ACTIVE,
                    remediation_op=cfg.OP_BLOCK_RESTORE,
                    remediation_state=cfg.STATE_BLOCKED,
                    verification_op=cfg.OP_VERIFY_RESTORE_BLOCKED,
                    verification_state=cfg.STATE_BLOCKED
                )

        # 6. RETAIN categories (SECURITY_AUDIT_LOG, LEGAL_HOLD_RECORD)
        elif cat_upper in ["SECURITY_AUDIT_LOG", "LEGAL_HOLD_RECORD"]:
            return PolicyEvaluationResult(
                is_compliant=True,
                required_state=cfg.STATE_PRESENT,
                verification_op=cfg.OP_VERIFY_RECORD_PRESENT,
                verification_state=cfg.STATE_PRESENT
            )

        # Default fallback
        return PolicyEvaluationResult(
            is_compliant=True,
            required_state=cfg.STATE_ABSENT,
            verification_op=cfg.OP_VERIFY_RECORD_ABSENT,
            verification_state=cfg.STATE_ABSENT
        )
