import json
import pandas as pd
from code.ingestion.csv_loader import CSVDataLoader
from code.identity.resolver import IdentityResolver
from code.evidence.indexer import EvidenceIndexer
from code.policy.rules_loader import PolicyRulesLoader
from code.policy.policy_engine import PolicyEngine
from code.agent.request_classifier import RequestClassifier
from code.agent.remediation_planner import RemediationPlanner
from code.agent.decision_engine import DeletionDecisionEngine
from code.evaluation.evaluate import Evaluator

# Let's inspect what accounts are mapped for each sample case
loader = CSVDataLoader("dataset")
df_samples = loader.load_sample_deletion_requests()
df_full = loader.load_deletion_requests()
df_manifest = loader.load_evidence_manifest()
df_act = loader.load_system_activity()
df_rules = loader.load_deletion_rules()
df_ident = loader.load_user_identities()
df_audit = loader.load_user_audit_log()
df_gold = pd.read_csv("dataset/sample_output.csv").set_index("case_id")

resolver = IdentityResolver(df_ident, df_audit)
indexer = EvidenceIndexer(loader.dataset_dir, df_manifest, df_act)

# Let's check Gold primary accounts for all 32 cases
gold_accounts = {}
for cid in df_samples["case_id"]:
    steps = json.loads(df_gold.loc[cid, "steps_json"])
    accs = [s["resource_id"] for s in steps if s["resource_id"].startswith("account_")]
    gold_accounts[cid] = accs[0] if accs else None

print("Gold accounts for samples:")
print(gold_accounts)
