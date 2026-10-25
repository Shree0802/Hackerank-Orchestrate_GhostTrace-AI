# Data Dictionary: Ghost Data Still Exists Deletion Audit

## 1. Overview
This document defines the schemas, semantics, entity relationships, timestamp conventions, and policy rules verified in the HackerRank Orchestrate (October 2026) challenge repository.

---

## 2. Core Tabular Datasets

### 2.1 `dataset/deletion_requests.csv` (518 evaluation rows)
- `case_id` (TEXT, PK): Unique case identifier (`case_33` through `case_550`).
- `email` (TEXT): Email provided in the deletion request. May match current email or a historical email.
- `requested_at` (ISO-8601 UTC): Submission timestamp of the customer request.
- `reported_status` (TEXT): Claim from internal deletion workflow (`COMPLETE`, `PARTIALLY_COMPLETE`, `NOT_STARTED`). Not authoritative evidence of true state.
- `reported_at` (ISO-8601 UTC): Timestamp when the internal workflow status was recorded.
- `audit_at` (ISO-8601 UTC): Audit cutoff timestamp. All decisions and evidence citations must be grounded in facts available at or before this timestamp (`captured_at <= audit_at`).
- `request_text` (TEXT): Verbatim customer message. Determines whether deletion was actually authorized.

### 2.2 `dataset/sample_deletion_requests.csv` (32 sample rows)
- Benchmark sample cases `case_01` through `case_32`.
- Corresponds to known golden answers in `dataset/sample_output.csv`.

### 2.3 `dataset/user_identities.csv` (850 users)
- `user_id` (TEXT, PK): Stable internal user reference (`user_01` through `user_850`).
- `name` (TEXT): Current full name.
- `email` (TEXT): Current primary email address.
- `phone` (TEXT): Current phone number (international format).
- `email_hash` (TEXT): SHA-256 hash of email.
- `updated_at` (ISO-8601 UTC): Snapshot update time.

### 2.4 `dataset/user_audit_log.csv` (306 historical change events)
- `audit_id` (TEXT, PK): Historical audit log identifier (`audit_01` through `audit_306`).
- `user_id` (TEXT, FK): Foreign key to `user_identities.user_id`.
- `event_time` (ISO-8601 UTC): Timestamp when the identity field change occurred.
- `field_name` (TEXT): Field changed (`email`, `phone`, `name`).
- `old_value` (TEXT): Value prior to the change. Used to resolve historical identifiers.
- `new_value` (TEXT): Value after the change.

### 2.5 `dataset/system_activity.csv` (4011 operational events)
- `activity_id` (TEXT, PK): Unique activity record identifier (`activity_01` through `activity_4011`).
- `event_time` (ISO-8601 UTC): Timestamp of the event.
- `event_type` (TEXT): `DELETE_RECORD`, `ANONYMIZE_RECORD`, `REDACT_RECORD`, `SYNC_RECORD`, `INDEX_RECORD`, `SEND_EMAIL`, `REFRESH_CACHE`, `RETAIN_RECORD`, `CREATE_EXPORT`, `CHECK_DATA_FLOW`, `DISABLE_DATA_FLOW`, `BLOCK_RESTORE`, `CHECK_RESTORE_ACCESS`, `LINK_RESOURCE_IDENTITY`, `CLASSIFY_REQUEST`, `RESTORE_BACKUP`.
- `source_system` (TEXT): Originating service (`deletion_worker`, `account_service`, `profile_service`, `support_platform`, `security_service`, `data_catalog`, etc.).
- `target_system` (TEXT): Receiving subsystem (`account_service`, `search_service`, `analytics_platform`, `integration_service`, `backup_service`, `identity_service`, `support_platform`, `export_service`, etc.).
- `resource_id` (TEXT): Target resource (`account_...`, `search_...`, `analytics_...`, `support_...`, `data_flow_...`, `backup_...`, `export_...`, `tombstone_...`, `audit_record_...`).
- `reported_result` (TEXT): `SUCCESS`, `PARTIAL`, `FAILED`. Note: Reported success is a claim; true state must be proven by evidence.
- `details` (TEXT): Detailed event description, including linkages to specific customer identifiers where applicable.

### 2.6 `dataset/deletion_rules.csv` (15 rules)
- `rule_01`: `USER_PROFILE` -> `DELETE`
- `rule_02`: `SECONDARY_IDENTIFIER` -> `DELETE`
- `rule_03`: `SEARCH_INDEX_ENTRY` -> `DELETE`
- `rule_04`: `CACHE_ENTRY` -> `DELETE`
- `rule_05`: `SUPPORT_MESSAGE` -> `REDACT` (conversation contains shared context)
- `rule_06`: `SUPPORT_ATTACHMENT` -> `DELETE` (attachment belongs only to deletion subject)
- `rule_07`: `ANALYTICS_PROFILE` -> `ANONYMIZE` (strip PII)
- `rule_08`: `PRODUCT_TELEMETRY` -> `ANONYMIZE`
- `rule_09`: `USER_EXPORT` -> `DELETE`
- `rule_10`: `MARKETING_PROFILE` -> `DELETE`
- `rule_11`: `EMAIL_DELIVERY_LOG` -> `REDACT`
- `rule_12`: `SECURITY_AUDIT_LOG` -> `RETAIN` (must remain present)
- `rule_13`: `LEGAL_HOLD_RECORD` -> `RETAIN`
- `rule_14`: `BACKUP_ARCHIVE` -> `RETAIN` (blocked restore)
- `rule_15`: `ACCOUNT_TOMBSTONE` -> `REDACT` (only stable user_id permitted; all direct PII redacted)

### 2.7 `dataset/evidence_files.csv` (94 files manifest)
- `file_id` (TEXT, PK): `evidence_01` through `evidence_94`.
- `file_path` (TEXT): Relative path under `evidence/`.
- `origin` (TEXT): Provenance of the evidence file.
- `captured_at` (ISO-8601 UTC): Point-in-time capture timestamp. Must be `<= audit_at` to be eligible for citing.

---

## 3. Evidence Artifact Formats

1. **Service Resource Exports (`service_resource_export_*.json`)**:
   Point-in-time JSON exports capturing records across `account_service`, `analytics_platform`, `backup_service`, `export_service`, `integration_service`, `search_service`, `security_service`, `support_platform`.
2. **Snapshot Bundles (`customer_data_snapshot_bundle_*.json`)**:
   Point-in-time snapshots of collections such as `deleted_customer_references` (tombstones), `security_audit_events`, `customer_profiles`.
3. **Database Dumps (`*.sql`)**:
   SQLite-compatible point-in-time database tables:
   - `customer_data_inventory_*.sql`: Full multi-service snapshot tables (`customer_profiles`, `customer_search_documents`, `customer_analytics_profiles`, `support_records`, `customer_exports`, `connector_subscriptions`, `backup_restore_entries`, `security_audit_records`).
   - `customer_data_read_replica_*.sql` & `customer_data_regional_replicas_*.sql`: Replicated tables for comparing replica drift.
   - `customer_accounts_failover_replica_*.sql`: Failover account snapshots.
   - `customer_search_primary_*.sql`: Primary search engine index tables.
4. **Shift Handover Summaries (`customer_account_handover_*.txt`)**:
   Explicit structured text log of audit checks with timestamp, system, resource ID, category, status, and user identifier.
5. **System Logs (`*.log`)**:
   - `resource_lookup_trace_*.log`: Key-value query traces with status code and returned row counts.
   - `structured_service_events_*.log`: JSON-line structured event streams.
   - `service_events_*.log`: Observability export logs.
   - `support_replica.log`: Support sync log.
6. **PDF Documents (`*.pdf`)**:
   - `delivery_correction_attachment.pdf`: Support attachment.
   - `legal_retention_register_*.pdf`: Legal hold records.
   - `security_retention_extract.pdf`: Compliance audit extract.
   - `account_history_report_*.pdf`: Export document.
7. **Console Screenshots (`*.png`)**:
   Rendered product UI screenshots mapped directly by `LINK_RESOURCE_IDENTITY` records in `system_activity.csv`.

---

## 4. Output Contract Schema

Output must be written to `output.csv` with exactly:
```csv
case_id,deletion_status,steps_json
```

Where:
- `case_id`: `case_33` through `case_550` (sorted ascending).
- `deletion_status`: `COMPLETE`, `INCOMPLETE`, or `NOT_APPLICABLE`.
- `steps_json`: JSON array of step objects. For `NOT_APPLICABLE`, `[]`.
- Each step object contains:
  - `step_no`: 1-based integer.
  - `phase`: `FINDING`, `REMEDIATION`, or `VERIFICATION`.
  - `system_id`: Subsystem name.
  - `resource_id`: Resource identifier.
  - `operation`: One of the 15 problem statement allowed operations.
  - `state`: Permitted target/current state (`PRESENT`, `ABSENT`, `REDACTED`, `ANONYMIZED`, `ACTIVE`, `DISABLED`, `BLOCKED`).
  - `evidence_id`:
    - For `COMPLETE` cases: Valid `file_id` proving current state.
    - For `INCOMPLETE` cases:
      - `FINDING`: Valid `file_id` proving violation/risk.
      - `REMEDIATION`: `""` (empty string).
      - `VERIFICATION`: `""` (empty string).
