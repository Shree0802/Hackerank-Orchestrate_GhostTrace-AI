import pandas as pd
import json

df_req = pd.read_csv('dataset/sample_deletion_requests.csv')
df_out = pd.read_csv('dataset/sample_output.csv')
df_u = pd.read_csv('dataset/user_identities.csv')
df_a = pd.read_csv('dataset/user_audit_log.csv')
df_act = pd.read_csv('dataset/system_activity.csv')

# Build mapping of all user identifiers
email_to_uid = {r['email'].lower(): r['user_id'] for _, r in df_u.iterrows()}
for _, r in df_a.iterrows():
    if r['field_name'] == 'email':
        email_to_uid[str(r['old_value']).lower()] = r['user_id']
        email_to_uid[str(r['new_value']).lower()] = r['user_id']

# For each sample case, let's see how its resources match activities
for _, r in df_req.iterrows():
    cid = r['case_id']
    req_em = r['email'].lower()
    uid = email_to_uid[req_em]
    t_req = r['requested_at']
    t_rep = r['reported_at']
    t_aud = r['audit_at']
    
    out_row = df_out[df_out['case_id'] == cid].iloc[0]
    expected_steps = json.loads(out_row['steps_json'])
    expected_rids = {s['resource_id']: (s['system_id'], s['operation'], s['state'], s['evidence_id']) for s in expected_steps}
    
    # Find all activities around this request
    # Specifically deletion_worker or related to this case
    # Let's inspect activities within [t_req - 1 hour, t_rep + 1 hour]
    act_window = df_act[(df_act['event_time'] >= t_req) & (df_act['event_time'] <= t_rep)]
    del_act = act_window[act_window['source_system'].isin(['deletion_worker', 'account_service', 'support_platform'])]
    
    # Check which expected resources are in del_act
    matched_in_window = set(del_act['resource_id']).intersection(expected_rids.keys())
    print(f"\n{cid} ({uid}) audit_at={t_aud} status={out_row['deletion_status']}:")
    print(f"  Expected resources ({len(expected_rids)}): {list(expected_rids.keys())}")
    print(f"  In activity window [{t_req} .. {t_rep}] ({len(matched_in_window)}): {list(matched_in_window)}")
    unmatched = set(expected_rids.keys()) - matched_in_window
    if unmatched:
        print(f"  NOT in activity window: {list(unmatched)}")
