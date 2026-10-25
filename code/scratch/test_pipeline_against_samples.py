import json
from pathlib import Path
import pandas as pd
from collections import defaultdict

from code.ingestion.csv_loader import CSVDataLoader
from code.identity.resolver import IdentityResolver
from code.evidence.indexer import EvidenceIndexer
from code.policy.rules_loader import PolicyRulesLoader
from code.policy.policy_engine import PolicyEngine
from code.agent.request_classifier import RequestClassifier
from code.ingestion.timestamp_utils import is_at_or_before, parse_iso_timestamp
import code.config as cfg

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

print("Indexer initialized. Evaluating against 32 samples...")

# Map of activity by window
del_acts = df_activity[df_activity['source_system'] == 'deletion_worker'].copy()
del_acts['dt'] = pd.to_datetime(del_acts['event_time'])

# Let's inspect each sample case
matches = 0
total_samples = len(df_samples)

for _, req in df_samples.iterrows():
    cid = req['case_id']
    email = req['email']
    req_text = req['request_text']
    subject = req['subject']
    t_req = req['requested_at']
    t_rep = req['reported_at']
    t_aud = req['audit_at']
    
    expected_row = df_sample_out[df_sample_out['case_id'] == cid].iloc[0]
    expected_status = expected_row['deletion_status']
    expected_steps = json.loads(expected_row['steps_json'])
    
    # 1. Classification
    is_del = RequestClassifier.is_deletion_request(req_text, subject)
    if not is_del:
        pred_status = cfg.STATUS_NOT_APPLICABLE
        pred_steps = []
    else:
        user = resolver.resolve_email(email)
        # Find expected resources to test reconstruction
        exp_rids = {s['resource_id']: s for s in expected_steps}
        pass

print("Test setup complete.")
