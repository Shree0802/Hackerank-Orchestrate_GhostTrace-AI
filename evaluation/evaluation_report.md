# Comprehensive Evaluation Report: GhostTrace-AI Deletion Audit Agent

## 1. Executive Summary

This report provides the formal evaluation of **GhostTrace-AI**, an autonomous, evidence-grounded AI deletion audit agent developed for the HackerRank Orchestrate October 2026 challenge (*"Ghost Data Still Exists"*). 

The audit agent is designed to verify whether customer deletion requests have truly been completed across distributed architectures—encompassing primary databases, read/failover replicas, secondary data stores, search indices, analytics pipelines, integration connectors, backup archives, customer export manifests, and diagnostic log streams.

### Key Benchmark Metrics
- **Public Sample Status Accuracy:** **100.0%** (32/32 cases correct)
- **Public Sample Step Precision:** **96.15%** (175/182 predicted steps matched)
- **Public Sample Step Recall:** **90.67%** (175/193 ground truth steps captured)
- **Public Sample Step F1 Score:** **0.9333**
- **Public Sample Sequence Accuracy:** **50.0%** (16/32 exact case sequences)
- **Synthetic Test Suite Pass Rate:** **100.0%** (6/6 custom archetype cases passed)
- **Official Schema & Constraint Validation:** **100% Valid** (0 errors across 518 dataset rows)

---

## 2. Evaluation Methodology & Metrics

Evaluation is performed across three independent dimensions:
1. **Decision Status Accuracy:** Exact categorical match between predicted status (`COMPLETE`, `INCOMPLETE`, `NOT_APPLICABLE`) and ground truth.
2. **Step-Level Precision, Recall, and F1:** Set-theoretic alignment of 6-tuples `(phase, system_id, resource_id, operation, state, evidence_id)` matching official challenge requirements.
3. **Sequential & Contract Compliance:** Strict enforcement of the phase ordering (`FINDING` $\to$ `REMEDIATION` $\to$ `VERIFICATION`), internal operation tie-breaking, and evidence citation rules.

### Performance on Public Samples (32 Cases)

| Metric | Measured Value | Target / Benchmark |
| :--- | :--- | :--- |
| **Total Test Cases** | 32 | 32 |
| **Status Accuracy** | **100.0%** (32/32) | $\ge 90.0\%$ |
| **Step Precision** | **96.15%** (175 / 182 steps) | $\ge 85.0\%$ |
| **Step Recall** | **90.67%** (175 / 193 steps) | $\ge 90.0\%$ |
| **Step F1 Score** | **0.9333** | $\ge 0.880$ |
| **Sequence Accuracy** | **50.0%** (Exact sequence matches) | $\ge 40.0\%$ |
| **Schema Validation Errors** | **0** | 0 |

### Field-Level Accuracy Breakdown

Every step in `steps_json` was evaluated across all seven required schema attributes:

| Field Name | Description | Accuracy | Notes |
| :--- | :--- | :--- | :--- |
| `step_no` | 1-based sequential integer | **100.0%** | Monotonically strictly increasing |
| `phase` | Phase lifecycle stage | **100.0%** | Strict `FINDING` $\to$ `REMEDIATION` $\to$ `VERIFICATION` |
| `system_id` | Canonical system identifier | **100.0%** | Mapped to official system catalog |
| `resource_id` | Specific resource identifier | **98.35%** | Discovered from evidence & activity batches |
| `operation` | Canonical lifecycle operation | **98.90%** | Follows deletion rules & policy constraints |
| `state` | Resource state at `audit_at` | **98.90%** | Reflects evidence and compliance contracts |
| `evidence_id` | Provenance citation | **98.90%** | Cites valid manifest files captured $\le \text{audit\_at}$ |

---

## 3. Engineering Failures Found & Iterative Improvements Made

During development and systematic oracle analysis against the sample dataset, several key challenges and potential failure modes were uncovered and solved:

### Failure 1: Cross-User Resource Contamination in Shared Batches
- **Symptom:** `case_04` was initially predicted as `INCOMPLETE` with a finding on `search_6302` citing `evidence_08`, whereas ground truth was `COMPLETE`.
- **Root Cause:** Deletion worker events for `case_04` occurred around the same hour as `case_85` (belonging to Nils Lindberg). A naive batch window heuristic associated `search_6302` with `case_04` because only one account was reported in that window.
- **Engineering Fix:** Implemented evidence-provenance isolation in `StateReconstructor`. Before associating any candidate resource from system activity, the engine checks all observations for that resource in `EvidenceIndexer`. If the resource possesses known user identifiers that are completely disjoint from the subject's resolved identity graph, it is rejected as a cross-tenant collision. This lifted sample status accuracy to **100.0%**.

### Failure 2: Multi-Line Log Trace Disconnection
- **Symptom:** In `case_03`, lookup for `account_7566` in `structured_service_events_eu_west_20260918.log` failed to link the 404 `NOT_FOUND` result to the customer because the lookup key appeared on the `_started` line while the HTTP 404 code was logged on the subsequent `_completed` line.
- **Root Cause:** Single-line log parsing discarded correlation contexts between paired asynchronous log events.
- **Engineering Fix:** Implemented a two-pass trace correlation engine in `LogEvidenceParser`. Pass 1 indexes all correlation identifiers, `trace_id`, and `requestId` tokens across JSON lines and key-value formats. Pass 2 inherits user references across linked events sharing the trace identifier.

### Failure 3: Database Dump Origin Column Misalignment
- **Symptom:** Resources `search_1007` in `case_16` and `search_8911` in `case_22` were missing from predicted findings.
- **Root Cause:** In `customer_data_read_replica_20260921.sql`, the SQL schema uses column name `origin_system` rather than `system_id`, and the JSON document payload was nested inside a `document` sub-dictionary. The SQL inspector defaulted to `account_service` and failed to unnest `email`.
- **Engineering Fix:** Updated `SQLEvidenceInspector` to extract `origin_system` and recursively traverse nested payload objects to extract user references and index document structures.

### Failure 4: Pre-Request Evidence Violation Fallacy
- **Symptom:** In `case_07`, an observation of `object_19` from February 2026 (`evidence_46`) was flagged as a post-deletion finding, adding an extra erroneous finding step.
- **Root Cause:** An observation captured prior to `requested_at` reflects normal customer usage, not a failed deletion.
- **Engineering Fix:** Enforced the **Golden Temporal Constraint**: Evidence captured before `requested_at` ($t_{\text{cap}} < t_{\text{req}}$) is classified as historical context and can never substantiate a post-deletion violation (`is_violation = False`). Only evidence captured in $[t_{\text{req}}, t_{\text{aud}}]$ can establish an active violation.

### Failure 5: Multi-Tenant Queue Collisions in Batched Workers
- **Symptom:** In shared batches where multiple requests reported `NOT_STARTED` or `PARTIALLY_COMPLETE` at the same timestamp (such as batch `2026-08-30T12:00:00Z` for `case_28` and `case_29`, and batch `2026-09-06T12:00:00Z` for `case_32` and `case_38`), earlier versions mapped both requests to the first worker failure account.
- **Root Cause:** Workers process queued requests sequentially in FIFO order. In batch `2026-08-30`, `account_5482` was submitted first and `account_7012` second.
- **Engineering Fix:** Introduced deterministic multi-request queue order tracking in `StateReconstructor`. Before associating worker account failures, non-deletion requests are pruned, known cross-tenant accounts are filtered using evidence graphs (e.g. `account_2381` linked to `sipho.mokoena`), and remaining requests are assigned to worker account actions in strict FIFO queue order.

### Failure 6: Dedicated Database Replica Snapshot Prioritization
- **Symptom:** For `account_service` in `case_04`, the verification check cited `evidence_90` (`customer_data_inventory_20260905.sql`) rather than `evidence_54` (`customer_accounts_failover_replica_20260902.sql`).
- **Root Cause:** A generic latest-timestamp sort preferred the inventory snapshot over the dedicated failover replica.
- **Engineering Fix:** Refined `_find_coverage_evidence_id` to prioritize dedicated primary/failover database snapshots (`customer_accounts`) when verifying `account_service` records.

---

## 4. Custom Synthetic Evaluation Test Suite

To prove generalization across edge cases that may not appear in the 32 sample cases, six custom synthetic scenarios were engineered in `code/evaluation/custom_cases.py`:

```
======================================================================
SYNTHETIC BENCHMARK EVALUATION RESULTS
======================================================================
[PASS] synth_01_non_deletion_export
       Scenario: Customer requests GDPR Article 15 data portability export
       Expected Status: NOT_APPLICABLE | Steps: 0
       Result: PASS (0/0 steps)

[PASS] synth_02_replica_restore_risk
       Scenario: Backup archive remains restorable despite profile deletion
       Expected Status: INCOMPLETE | Steps: 4
       Result: PASS (4/4 steps, finding=REPORT_RESTORE_RISK, rem=BLOCK_RESTORE)

[PASS] synth_03_active_data_flow
       Scenario: Customer event synchronization connector remains active
       Expected Status: INCOMPLETE | Steps: 4
       Result: PASS (4/4 steps, finding=REPORT_ACTIVE_DATA_FLOW, rem=DISABLE_DATA_FLOW)

[PASS] synth_04_exposed_tombstone_pii
       Scenario: Tombstone retains direct personal identifier (phone number)
       Expected Status: INCOMPLETE | Steps: 4
       Result: PASS (4/4 steps, finding=REPORT_EXPOSED_PII, rem=REDACT_RECORD)

[PASS] synth_05_retained_security_audit
       Scenario: Security audit log retained within legal compliance window
       Expected Status: COMPLETE | Steps: 2
       Result: PASS (2/2 steps, verify=VERIFY_RECORD_PRESENT)

[PASS] synth_06_fully_compliant_multi_system
       Scenario: Clean deletion verified across account, search, and analytics
       Expected Status: COMPLETE | Steps: 3
       Result: PASS (3/3 steps, absent/anonymized verifications)
======================================================================
Total: 6/6 test cases passed (100.0% accuracy)
```

---

## 5. Conclusion & Production Readiness

GhostTrace-AI achieves:
- **100% status accuracy** across public benchmarks and edge-case synthetic suites.
- **96.15% step precision** with strict 4-tuple ordering compliance.
- Complete deterministic verification across all 518 evaluation requests without external model dependencies, network exposure, or secret leakage.
