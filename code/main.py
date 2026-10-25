"""Main CLI entry point for the AI-Powered Deletion Audit Agent."""

import argparse
import json
import sys
from pathlib import Path

from code.ingestion.csv_loader import CSVDataLoader
from code.identity.resolver import IdentityResolver
from code.evidence.indexer import EvidenceIndexer
from code.policy.rules_loader import PolicyRulesLoader
from code.policy.policy_engine import PolicyEngine
from code.audit.state_reconstructor import StateReconstructor
from code.agent.remediation_planner import RemediationPlanner
from code.agent.decision_engine import DeletionDecisionEngine
from code.output.serializer import OutputSerializer
from code.output.validator import OutputValidator
from code.evaluation.evaluate import Evaluator
from code.evaluation.custom_cases import run_custom_evaluations

def build_engine(dataset_dir: Path) -> DeletionDecisionEngine:
    """Build and initialize the end-to-end audit engine from the dataset directory."""
    loader = CSVDataLoader(dataset_dir)
    df_identities = loader.load_user_identities()
    df_audit_log = loader.load_user_audit_log()
    df_manifest = loader.load_evidence_manifest()
    df_activity = loader.load_system_activity()
    df_rules = loader.load_deletion_rules()

    resolver = IdentityResolver(df_identities, df_audit_log)
    indexer = EvidenceIndexer(dataset_dir, df_manifest, df_activity, resolver=resolver)
    policy_engine = PolicyEngine(PolicyRulesLoader(df_rules))
    reconstructor = StateReconstructor(df_activity, df_manifest, indexer, dataset_dir=dataset_dir)
    planner = RemediationPlanner(policy_engine)
    return DeletionDecisionEngine(resolver, reconstructor, planner)

def process_requests(engine: DeletionDecisionEngine, df_requests, output_path: Path, validate: bool = True):
    """Process requests, serialize to CSV, and validate compliance."""
    results = []
    total = len(df_requests)
    for idx, (_, req) in enumerate(df_requests.iterrows(), 1):
        res = engine.process_request(req)
        results.append(res)
        if idx % 50 == 0 or idx == total:
            print(f"Processed {idx}/{total} requests...")

    OutputSerializer.serialize_to_csv(results, output_path)
    print(f"Successfully wrote {len(results)} rows to {output_path}")

    if validate:
        val = OutputValidator.validate_file(output_path, expected_count=len(results))
        if val.is_valid:
            print(f"[OK] Validation passed: {len(results)} rows compliant with official schema and rules.")
        else:
            print(f"[ERROR] Validation failed with {len(val.errors)} errors:")
            for err in val.errors[:10]:
                print(f"  - {err}")
            sys.exit(1)

def evaluate_samples(dataset_dir: Path):
    """Evaluate predictions on sample requests against the sample ground truth."""
    loader = CSVDataLoader(dataset_dir)
    df_samples = loader.load_sample_deletion_requests()
    gold_path = dataset_dir / "sample_output.csv"
    if not gold_path.exists():
        print(f"Sample output file not found at {gold_path}")
        sys.exit(1)

    print("Initializing engine for sample evaluation...")
    engine = build_engine(dataset_dir)
    tmp_pred_path = Path("code/scratch/sample_predictions.csv")
    process_requests(engine, df_samples, tmp_pred_path, validate=True)

    metrics = Evaluator.evaluate_files(tmp_pred_path, gold_path)
    print("\n" + "=" * 50)
    print("SAMPLE EVALUATION SUMMARY")
    print("=" * 50)
    print(json.dumps(metrics.summary_dict(), indent=2))
    print("=" * 50)

def main():
    parser = argparse.ArgumentParser(
        description="GhostTrace-AI: AI-Powered Deletion Audit Agent"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="dataset",
        help="Path to dataset directory (default: dataset)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output.csv",
        help="Path to output CSV file (default: output.csv)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate output CSV against official schema and constraint rules",
    )
    parser.add_argument(
        "--evaluate-samples",
        action="store_true",
        help="Run evaluation on sample_deletion_requests.csv against sample_output.csv",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Run synthetic evaluation test cases",
    )

    args = parser.parse_args()
    dataset_dir = Path(args.dataset)

    if args.evaluate:
        print("Running synthetic evaluation test cases...")
        results = run_custom_evaluations()
        passed = sum(1 for r in results if r["passed"])
        print(f"Synthetic evaluation: {passed}/{len(results)} test cases passed.")
        return

    if args.evaluate_samples:
        evaluate_samples(dataset_dir)
        return

    if not dataset_dir.exists():
        print(f"Error: Dataset directory '{dataset_dir}' does not exist.")
        sys.exit(1)

    loader = CSVDataLoader(dataset_dir)
    df_requests = loader.load_deletion_requests()
    print(f"Loaded {len(df_requests)} deletion requests from {dataset_dir / 'deletion_requests.csv'}")

    print("Initializing audit engine...")
    engine = build_engine(dataset_dir)

    output_path = Path(args.output)
    process_requests(engine, df_requests, output_path, validate=args.validate or True)

if __name__ == "__main__":
    main()
