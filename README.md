# GhostTrace-AI: AI-Powered Deletion Audit Agent
**HackerRank Orchestrate October 2026 Challenge — *"Ghost Data Still Exists"***

An evidence-grounded, production-grade AI deletion audit agent that investigates whether customer personal data has truly been deleted across complex, distributed enterprise architectures.

---

## Architecture Overview

```
Input CSVs & Evidence Files
          │
          ▼
┌─────────────────────────────────┐
│   Data Ingestion & Loaders      │ ◄── csv_loader, timestamp_utils
└─────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│ Multi-Modal Evidence Indexer    │ ◄── SQL dumps, JSON bundles, logs, PDFs, PNGs
└─────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│    Identity Graph Resolver      │ ◄── Current & historical aliases, email hashes
└─────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│ Temporal State Reconstructor    │ ◄── Evaluates true state strictly at audit_at
└─────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│  Policy Engine & Planner        │ ◄── Deletion rules 1-15, 4-tuple sorting contract
└─────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│ Output Serializer & Validator   │ ◄── Strict schema, evidence provenance, steps_json
└─────────────────────────────────┘
          │
          ▼
    output.csv (518 cases)
```

---

## Quick Start & CLI Commands

### 1. Requirements & Setup
The project requires Python 3.10+ and standard data processing dependencies:
```bash
pip install -r requirements.txt
```
*(Dependencies: `pandas`, `pymupdf`)*

### 2. Run Audit on Full Dataset (518 Requests)
Generates `output.csv` at the repository root and performs strict rule validation:
```bash
python -m code.main --dataset dataset --output output.csv --validate
```

### 3. Evaluate on 32 Public Samples
Runs end-to-end audit on `sample_deletion_requests.csv` and computes precision, recall, F1, and status accuracy against `sample_output.csv`:
```bash
python -m code.main --evaluate-samples
```
**Results:**
- **Status Accuracy:** **100.0%** (32/32 exact matches)
- **Step Precision:** **96.15%** (175/182 matched steps)
- **Step Recall:** **90.67%** (175/193 matched steps)
- **Step F1 Score:** **0.9333**
- **Sequence Accuracy:** **50.0%** (16/32 exact sequence matches)

### 4. Run Synthetic Edge-Case Benchmarks
Runs 6 custom scenario archetypes covering non-deletion, backup restore risks, sync connector flows, exposed tombstone PII, retained audit records, and multi-system compliant deletion:
```bash
python -m code.main --evaluate
```
**Results:** **6 / 6 (100.0%) Passed**

### 5. Run Automated Unit Test Suite
Runs the 28 comprehensive unit and integration tests across parsers, classifiers, identity resolution, ordering contracts, and output validation:
```bash
python -m unittest discover code/tests
```
**Results:** **28 / 28 Passed (OK)**

---

## Core Technical Features

1. **Deterministic Request Classification:**
   - Multi-lingual grammar and regex classifier separating actual deletion requests from data export inquiries, terms of service requests, and profile maintenance.
   - Accurately classifies non-deletion requests (`case_533` – `case_542`) as `NOT_APPLICABLE` with `steps_json=[]`.

2. **Temporal Multi-Modal Evidence Indexer:**
   - Ingests and indexes 94 heterogeneous evidence files including SQLite dumps, JSON bundles, diagnostic logs, PyMuPDF-parsed PDF attachments, and console screenshots.
   - Implements two-pass trace correlation linking asynchronous `_started` and `_completed` log events by `trace_id` and `requestId`.
   - Distinguishes pre-request normal activity ($t < t_{\text{req}}$) from post-deletion violations in $[t_{\text{req}}, t_{\text{aud}}]$.

3. **Identity Graph Resolver:**
   - Tracks current and historical identifiers (emails, names, phone numbers, SHA-256 email hashes).
   - Prevents cross-tenant entity collisions in shared deletion worker batches using evidence-provenance verification.

4. **Policy Engine & Remediation Planner:**
   - Evaluates compliance against organizational deletion rules 1–15.
   - Enforces the strict sorting contract:
     - Phases: `FINDING` (1) $\to$ `REMEDIATION` (2) $\to$ `VERIFICATION` (3).
     - Operations ordered by policy lifecycle priority.
     - Tie-breaking: `system_id` ASC, then `resource_id` ASC.

5. **Strict Constraint Validation:**
   - `COMPLETE`: Only `VERIFICATION` steps exist, all citing valid evidence IDs captured $\le t_{\text{aud}}$.
   - `INCOMPLETE`: `FINDING` steps cite the valid evidence ID of the violation; `REMEDIATION` and `VERIFICATION` steps have `evidence_id: ""`.
   - Step numbers strictly consecutive integers starting from 1.

---

## Submission Artifacts

- **`output.csv`**: Contains exactly 518 data rows (`case_33` to `case_550`) sorted by `case_id`.
- **`code.zip`**: Contains `code/`, `README.md`, `code/evaluation/evaluation_report.md`, and `code/evaluation/usage_report.md`.
- **`log.txt`**: Complete audit turn session log tracking all engineering activities conforming to `AGENTS.md`.

---

## Packaging Instructions

To create the clean submission archive `code.zip` (excluding `dataset/`, `.venv`, and `__pycache__`):

**Windows (PowerShell):**
```powershell
python -c "import shutil, os; [shutil.rmtree(os.path.join(r, d)) for r, d, _ in os.walk('code') if d == '__pycache__']"
Compress-Archive -Path README.md, code -DestinationPath code.zip -Force
```

**Linux / macOS:**
```bash
zip -r code.zip README.md code -x "*/__pycache__/*" "*/.venv/*" "*/.git/*"
```
