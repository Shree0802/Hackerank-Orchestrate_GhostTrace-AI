import json
from pathlib import Path
import pandas as pd

from code.ingestion.csv_loader import CSVDataLoader
from code.identity.resolver import IdentityResolver
from code.evidence.indexer import EvidenceIndexer
from code.ingestion.timestamp_utils import is_at_or_before, parse_iso_timestamp

loader = CSVDataLoader(Path('dataset'))
df_identities = loader.load_user_identities()
df_audit_log = loader.load_user_audit_log()
df_manifest = loader.load_evidence_manifest()
df_activity = loader.load_system_activity()
df_samples = loader.load_sample_deletion_requests()
df_sample_out = pd.read_csv('dataset/sample_output.csv')

resolver = IdentityResolver(df_identities, df_audit_log)
indexer = EvidenceIndexer(Path('dataset'), df_manifest, df_activity)

del_acts = df_activity[df_activity['source_system'] == 'deletion_worker'].copy()
del_acts['dt'] = pd.to_datetime(del_acts['event_time'])

perfect_matches = 0

for _, req in df_samples.iterrows():
    cid = req['case_id']
    user = resolver.resolve_email(req['email'])
    t_req = req['requested_at']
    t_rep = req['reported_at']
    t_aud = req['audit_at']
    
    gold_row = df_sample_out[df_sample_out['case_id'] == cid].iloc[0]
    gold_steps = json.loads(gold_row['steps_json'])
    gold_rids = set(s['resource_id'] for s in gold_steps)
    
    # 1. Observations in [t_req, t_aud]
    obs_in_window = [
        o['resource_id'] for o in indexer.get_observations_for_user(user, t_aud)
        if is_at_or_before(t_req, o['captured_at']) and o.get('resource_id')
    ]
    
    # 2. Primary account
    user_num_str = user.user_id.replace("user_", "")
    conv_acc = f"account_{int(user_num_str):03d}" if user_num_str.isdigit() else None
    
    # Check deletion worker around reported_at
    t_rep_dt = pd.to_datetime(t_rep)
    nearby_acts = del_acts[(del_acts['dt'] >= t_rep_dt - pd.Timedelta(hours=1, minutes=30)) & (del_acts['dt'] <= t_rep_dt + pd.Timedelta(minutes=30))]
    
    candidate_rids = set(obs_in_window)
    # Add account if matches
    for _, a in nearby_acts.iterrows():
        rid = str(a.get('resource_id', ''))
        if rid.startswith('account_'):
            if rid == conv_acc or len(nearby_acts[nearby_acts['resource_id'].str.startswith('account_')]) == 1:
                candidate_rids.add(rid)
        elif not rid.startswith('account_'):
            # Check if details mention user
            det = str(a.get('details', ''))
            if user.user_id in det or any(em in det for em in user.all_emails):
                candidate_rids.add(rid)
            elif len(nearby_acts[nearby_acts['resource_id'].str.startswith('account_')]) == 1:
                candidate_rids.add(rid)

    # If no account added yet, add conv_acc
    has_acc = any(r.startswith('account_') for r in candidate_rids)
    if not has_acc and conv_acc:
        candidate_rids.add(conv_acc)

    # Also check audit_record
    # If case >= 11, check audit record for user
    all_user_obs = indexer.get_observations_for_user(user, "2026-12-31T23:59:59Z")
    for o in all_user_obs:
        rid = o.get('resource_id', '')
        if rid.startswith('audit_record_'):
            candidate_rids.add(rid)

    overlap = candidate_rids.intersection(gold_rids)
    diff = gold_rids ^ candidate_rids
    if not diff:
        perfect_matches += 1
    else:
        print(f"{cid} ({user.user_id}): missing in pred={gold_rids - candidate_rids} | extra in pred={candidate_rids - gold_rids}")

print(f"\nPerfect resource set matches: {perfect_matches}/32")
