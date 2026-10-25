import json
import pandas as pd
from code.ingestion.csv_loader import CSVDataLoader
from code.identity.resolver import IdentityResolver
from code.evidence.indexer import EvidenceIndexer
from code.policy.policy_engine import PolicyEngine
from code.agent.request_classifier import RequestClassifier
from code.agent.remediation_planner import RemediationPlanner
from code.audit.state_reconstructor import StateReconstructor
from code.agent.decision_engine import DecisionEngine
from code.evaluation.evaluate import Evaluator

loader = CSVDataLoader("dataset")
df_reqs = loader.load_sample_deletion_requests()
df_manifest = loader.load_evidence_manifest()
df_activity = loader.load_system_activity()
df_identities = loader.load_user_identities()
df_audit_log = loader.load_user_audit_log()
df_rules = loader.load_deletion_rules()

resolver = IdentityResolver(df_identities, df_audit_log)
indexer = EvidenceIndexer(loader.dataset_dir, df_manifest, df_activity)
classifier = RequestClassifier()
policy_engine = PolicyEngine(df_rules)
planner = RemediationPlanner(policy_engine)
reconstructor = StateReconstructor(df_activity, df_manifest, indexer)
engine = DecisionEngine(classifier, resolver, reconstructor, planner)

# Test running on sample requests
results = []
for _, row in df_reqs.iterrows():
    res = engine.audit_request(
        case_id=row["case_id"],
        email=row["email"],
        requested_at=row["requested_at"],
        reported_status=row["reported_status"],
        reported_at=row["reported_at"],
        audit_at=row["audit_at"],
        request_text=row["request_text"],
    )
    results.append({
        "case_id": res.case_id,
        "deletion_status": res.deletion_status,
        "steps_json": json.dumps(res.steps_json)
    })

df_pred = pd.DataFrame(results)
evaluator = Evaluator(df_gold_path="dataset/sample_output.csv")
metrics = evaluator.evaluate(df_pred)
print("Current metrics:")
print(json.dumps(metrics, indent=2))
