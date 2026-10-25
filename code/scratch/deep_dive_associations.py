import pandas as pd
import json
import glob
import os
import re

df_req = pd.read_csv('dataset/sample_deletion_requests.csv')
df_out = pd.read_csv('dataset/sample_output.csv')
df_u = pd.read_csv('dataset/user_identities.csv')
df_a = pd.read_csv('dataset/user_audit_log.csv')
df_act = pd.read_csv('dataset/system_activity.csv')

# Build user identifiers lookup
user_info = {}
for _, r in df_u.iterrows():
    uid = r['user_id']
    user_info[uid] = {
        'user_id': uid,
        'emails': {r['email'].lower()},
        'phones': {str(r['phone'])},
        'names': {str(r['name'])},
        'hashes': {str(r['email_hash'])}
    }

for _, r in df_a.iterrows():
    uid = r['user_id']
    if uid in user_info:
        fn = r['field_name']
        if fn == 'email':
            user_info[uid]['emails'].add(str(r['old_value']).lower())
            user_info[uid]['emails'].add(str(r['new_value']).lower())
        elif fn == 'phone':
            user_info[uid]['phones'].add(str(r['old_value']))
            user_info[uid]['phones'].add(str(r['new_value']))
        elif fn == 'name':
            user_info[uid]['names'].add(str(r['old_value']))
            user_info[uid]['names'].add(str(r['new_value']))

email_to_uid = {}
for uid, info in user_info.items():
    for em in info['emails']:
        email_to_uid[em] = uid

# Now check each sample case resources
sample_res_sources = {}
for _, r in df_req.iterrows():
    cid = r['case_id']
    em = r['email'].lower()
    uid = email_to_uid[em]
    steps = json.loads(df_out[df_out['case_id'] == cid]['steps_json'].iloc[0])
    expected_resources = set(s['resource_id'] for s in steps)
    
    # Where does each resource appear in system_activity?
    act_matches = df_act[df_act['resource_id'].isin(expected_resources)]
    
    print(f"\n{cid} ({uid}, {em}): expected {len(expected_resources)} resources: {expected_resources}")
    print(f"  Matches in system_activity: {set(act_matches['resource_id'])}")
    missing = expected_resources - set(act_matches['resource_id'])
    if missing:
        print(f"  NOT in system_activity: {missing}")
