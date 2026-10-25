import pandas as pd
import json
from pathlib import Path
from code.ingestion.csv_loader import CSVDataLoader
from code.identity.resolver import IdentityResolver
from code.evidence.indexer import EvidenceIndexer
from code.ingestion.timestamp_utils import is_at_or_before

loader = CSVDataLoader(Path('dataset'))
df_identities = loader.load_user_identities()
df_audit_log = loader.load_user_audit_log()
df_manifest = loader.load_evidence_manifest()
df_activity = loader.load_system_activity()
df_samples = loader.load_sample_deletion_requests()
df_sample_out = pd.read_csv('dataset/sample_output.csv')

resolver = IdentityResolver(df_identities, df_audit_log)
indexer = EvidenceIndexer(Path('dataset'), df_manifest, df_activity)

# Inspect all 32 sample cases
total_expected_resources = 0
found_by_direct_ident = 0
found_by_activity = 0
not_found = []

for _, req in df_samples.iterrows():
    cid = req['case_id']
    u = resolver.resolve_email(req['email'])
    out_row = df_sample_out[df_sample_out['case_id'] == cid].iloc[0]
    steps = json.loads(out_row['steps_json'])
    
    # 1. Direct observations from indexer
    obs_direct = indexer.get_observations_for_user(u, req['audit_at'])
    direct_rids = {o['resource_id'] for o in obs_direct if o.get('resource_id')}
    
    # 2. Activity in window
    window_acts = df_activity[(df_activity['event_time'] >= req['requested_at']) & (df_activity['event_time'] <= req['reported_at'])]
    act_rids = set(window_acts['resource_id'].dropna())
    
    # Also check link_resource_identity
    link_acts = df_activity[df_activity['event_type'] == 'LINK_RESOURCE_IDENTITY']
    for _, l in link_acts.iterrows():
        if u.matches_identifier(str(l['resource_id'])) or u.matches_identifier(str(l['details'])):
            pass
            
    for s in steps:
        total_expected_resources += 1
        rid = s['resource_id']
        if rid in direct_rids:
            found_by_direct_ident += 1
        elif rid in act_rids:
            found_by_activity += 1
        else:
            not_found.append((cid, u.user_id, rid, s['system_id'], s['operation'], s['state'], s['evidence_id']))

print(f"Total expected resources across 32 samples: {total_expected_resources}")
print(f"Found by direct identifier: {found_by_direct_ident}")
print(f"Found by window activity: {found_by_activity}")
print(f"Not found yet: {len(not_found)}")
for nf in not_found:
    print(" ", nf)
