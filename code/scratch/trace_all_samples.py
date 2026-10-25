import pandas as pd
import json
import glob
import os

df_req = pd.read_csv('dataset/sample_deletion_requests.csv')
df_out = pd.read_csv('dataset/sample_output.csv')
df_ident = pd.read_csv('dataset/user_identities.csv')
df_audit = pd.read_csv('dataset/user_audit_log.csv')
df_ev = pd.read_csv('dataset/evidence_files.csv')
ev_map = dict(zip(df_ev['file_id'], df_ev['file_path']))

# Build email to user_id mapping
email_to_user = {}
for _, r in df_ident.iterrows():
    email_to_user[r['email'].lower()] = r['user_id']
# Also check audit log
for _, r in df_audit.iterrows():
    if r['field_name'] == 'email':
        email_to_user[str(r['old_value']).lower()] = r['user_id']
        email_to_user[str(r['new_value']).lower()] = r['user_id']

for _, r in df_req.iterrows():
    cid = r['case_id']
    email = r['email'].lower()
    uid = email_to_user.get(email, 'UNKNOWN')
    out_row = df_out[df_out['case_id'] == cid].iloc[0]
    steps = json.loads(out_row['steps_json'])
    evs = set(s['evidence_id'] for s in steps if s['evidence_id'])
    
    # print case info
    print(f"\n{cid}: {email} -> {uid} | reported: {r['reported_status']} | status: {out_row['deletion_status']} | audit_at: {r['audit_at']}")
    print(f"  Cited: {[(ev, ev_map.get(ev)) for ev in evs]}")
    for s in steps:
        print(f"    [{s['phase']}] {s['system_id']} / {s['resource_id']}: {s['operation']} -> {s['state']} (ev: {s['evidence_id']})")
