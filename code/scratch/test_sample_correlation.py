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

for _, r in df_req.iterrows():
    cid = r['case_id']
    req_em = r['email'].lower()
    uid = email_to_uid[req_em]
    t_req = r['requested_at']
    t_rep = r['reported_at']
    t_aud = r['audit_at']
    
    out_row = df_out[df_out['case_id'] == cid].iloc[0]
    expected_steps = json.loads(out_row['steps_json'])
    
    # 1. Activities in [t_req, t_rep]
    window_acts = df_act[(df_act['event_time'] >= t_req) & (df_act['event_time'] <= t_rep)]
    # Deletion worker or account deletion activities
    dw_acts = window_acts[window_acts['source_system'].isin(['deletion_worker', 'account_service'])]
    
    print(f"\n=== {cid} ({uid}) audit_at={t_aud} status={out_row['deletion_status']} ===")
    print("  Expected steps:")
    for s in expected_steps:
        print(f"    {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | {s['evidence_id']}")
    print("  Deletion worker activities in window:")
    for _, a in dw_acts.iterrows():
        print(f"    {a['event_time']} | {a['event_type']} | {a['target_system']} | {a['resource_id']} | {a['details']}")
