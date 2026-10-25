import json
from pathlib import Path
import pandas as pd

from code.ingestion.csv_loader import CSVDataLoader
from code.identity.resolver import IdentityResolver
from code.evidence.indexer import EvidenceIndexer
from code.policy.rules_loader import PolicyRulesLoader
from code.policy.policy_engine import PolicyEngine
from code.ingestion.timestamp_utils import is_at_or_before, parse_iso_timestamp

loader = CSVDataLoader(Path('dataset'))
df_identities = loader.load_user_identities()
df_audit_log = loader.load_user_audit_log()
df_manifest = loader.load_evidence_manifest()
df_activity = loader.load_system_activity()
df_rules = loader.load_deletion_rules()
df_samples = loader.load_sample_deletion_requests()
df_sample_out = pd.read_csv('dataset/sample_output.csv')

resolver = IdentityResolver(df_identities, df_audit_log)
indexer = EvidenceIndexer(Path('dataset'), df_manifest, df_activity)
policy_engine = PolicyEngine(PolicyRulesLoader(df_rules))

print("Indexer built with", len(indexer.all_observations), "observations.")

# Check all 32 sample cases
for _, req in df_samples.iterrows():
    cid = req['case_id']
    email = req['email']
    t_req = req['requested_at']
    t_rep = req['reported_at']
    t_aud = req['audit_at']
    
    expected_row = df_sample_out[df_sample_out['case_id'] == cid].iloc[0]
    expected_status = expected_row['deletion_status']
    expected_steps = json.loads(expected_row['steps_json'])
    
    user = resolver.resolve_email(email)
    
    # 1. Direct observations for user
    obs = indexer.get_observations_for_user(user, t_aud)
    
    print(f"\n{cid} ({user.user_id}) exp_status={expected_status} steps={len(expected_steps)} obs={len(obs)}")
