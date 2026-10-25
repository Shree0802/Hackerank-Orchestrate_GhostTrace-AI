import json
from pathlib import Path
import pandas as pd

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

loader = CSVDataLoader(Path('dataset'))
df_identities = loader.load_user_identities()
df_audit_log = loader.load_user_audit_log()
df_manifest = loader.load_evidence_manifest()
df_activity = loader.load_system_activity()
df_rules = loader.load_deletion_rules()
df_samples = loader.load_sample_deletion_requests()

resolver = IdentityResolver(df_identities, df_audit_log)
indexer = EvidenceIndexer(Path('dataset'), df_manifest, df_activity)
policy_engine = PolicyEngine(PolicyRulesLoader(df_rules))
reconstructor = StateReconstructor(df_activity, df_manifest, indexer)
planner = RemediationPlanner(policy_engine)
engine = DeletionDecisionEngine(resolver, reconstructor, planner)

# Run prediction for all samples
results = []
for _, req in df_samples.iterrows():
    res = engine.process_request(req)
    results.append(res)

sample_pred_path = Path("code/scratch/sample_predictions.csv")
OutputSerializer.serialize_to_csv(results, sample_pred_path)

val = OutputValidator.validate_file(sample_pred_path, expected_count=32)
print("Validation is_valid:", val.is_valid)
if val.errors:
    print("Validation errors:", val.errors[:5])

metrics = Evaluator.evaluate_files(sample_pred_path, Path("dataset/sample_output.csv"))
print("Sample evaluation summary:")
print(json.dumps(metrics.summary_dict(), indent=2))

for d in metrics.case_details:
    if not d.get("exact_match"):
        print(f"Mismatch in {d['case_id']}: gold_status={d.get('gold_status')} pred_status={d.get('pred_status')} gold_steps={d.get('gold_steps_count')} pred_steps={d.get('pred_steps_count')}")
