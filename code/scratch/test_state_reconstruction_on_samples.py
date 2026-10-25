import pandas as pd
import json
from pathlib import Path
from code.ingestion.csv_loader import CSVDataLoader
from code.identity.resolver import IdentityResolver
from code.evidence.indexer import EvidenceIndexer
from code.policy.rules_loader import PolicyRulesLoader
from code.policy.policy_engine import PolicyEngine
from code.ingestion.timestamp_utils import is_at_or_before

dataset_dir = Path("dataset")
loader = CSVDataLoader(dataset_dir)
df_manifest = loader.load_evidence_manifest()
df_activity = loader.load_system_activity()
df_identities = loader.load_user_identities()
df_audit_log = loader.load_user_audit_log()
df_rules = loader.load_deletion_rules()

resolver = IdentityResolver(df_identities, df_audit_log)
indexer = EvidenceIndexer(dataset_dir, df_manifest, df_activity)
rules_loader = PolicyRulesLoader(df_rules)
policy_engine = PolicyEngine(rules_loader)

df_samples = loader.load_sample_deletion_requests()
df_sample_out = pd.read_csv("dataset/sample_output.csv")

print("Ready to test state reconstruction on samples...")
