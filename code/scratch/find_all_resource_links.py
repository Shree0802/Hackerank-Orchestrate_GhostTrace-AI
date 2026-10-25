import pandas as pd
import json
import glob
import os
import re

df_req = pd.read_csv('dataset/sample_deletion_requests.csv')
df_out = pd.read_csv('dataset/sample_output.csv')
df_u = pd.read_csv('dataset/user_identities.csv')
df_a = pd.read_csv('dataset/user_audit_log.csv')

# Build mapping of all user identifiers
user_ids = {}
for _, r in df_u.iterrows():
    uid = r['user_id']
    user_ids[uid] = {
        'user_id': uid,
        'email': r['email'].lower(),
        'all_emails': {r['email'].lower()},
        'phone': str(r['phone']),
        'name': str(r['name']),
        'hash': str(r['email_hash'])
    }

for _, r in df_a.iterrows():
    uid = r['user_id']
    if uid in user_ids and r['field_name'] == 'email':
        user_ids[uid]['all_emails'].add(str(r['old_value']).lower())
        user_ids[uid]['all_emails'].add(str(r['new_value']).lower())

email_to_uid = {}
for uid, d in user_ids.items():
    for em in d['all_emails']:
        email_to_uid[em] = uid

# Now let's check for each sample case:
# What are all the evidence files and where do the resources appear?
all_evidence_files = glob.glob('dataset/evidence/**/*.*', recursive=True)

for _, r in df_req.iterrows():
    cid = r['case_id']
    req_em = r['email'].lower()
    uid = email_to_uid[req_em]
    uinfo = user_ids[uid]
    
    out_row = df_out[df_out['case_id'] == cid].iloc[0]
    steps = json.loads(out_row['steps_json'])
    expected_resources = {s['resource_id']: s for s in steps}
    
    print(f"\n=== {cid} | {uid} | {req_em} ===")
    for rid, s in expected_resources.items():
        # Search which evidence files contain this rid
        found_in = []
        for ef in all_evidence_files:
            try:
                with open(ef, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if rid in content:
                        found_in.append(os.path.basename(ef))
            except:
                pass
        print(f"  {rid:<20} ({s['system_id']:<18}) expected_state={s['state']:<10} found in: {found_in}")
