import pandas as pd
import json

df_req = pd.read_csv('dataset/sample_deletion_requests.csv')
df_out = pd.read_csv('dataset/sample_output.csv')
df_u = pd.read_csv('dataset/user_identities.csv')
df_a = pd.read_csv('dataset/user_audit_log.csv')

email_to_uid = {r['email'].lower(): r['user_id'] for _, r in df_u.iterrows()}
for _, r in df_a.iterrows():
    if r['field_name'] == 'email':
        email_to_uid[str(r['old_value']).lower()] = r['user_id']
        email_to_uid[str(r['new_value']).lower()] = r['user_id']

for _, r in df_req.iterrows():
    cid = r['case_id']
    em = r['email'].lower()
    uid = email_to_uid.get(em, 'UNKNOWN')
    steps = json.loads(df_out[df_out['case_id'] == cid]['steps_json'].iloc[0])
    
    audit_steps = [s for s in steps if 'audit' in s['resource_id'] or s['system_id'] == 'security_service']
    if audit_steps:
        # Check user_audit_log for this user
        u_audits = df_a[df_a['user_id'] == uid]
        audit_ids = list(u_audits['audit_id'])
        print(f"{cid} | {uid} | {em}:")
        for s in audit_steps:
            print(f"  Step: {s['resource_id']} | ev: {s['evidence_id']}")
        print(f"  user_audit_log rows: {len(u_audits)} -> {audit_ids}")
