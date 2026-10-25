import pandas as pd
import json
import glob
import os
import re

df_req = pd.read_csv('dataset/deletion_requests.csv')
df_u = pd.read_csv('dataset/user_identities.csv')
df_a = pd.read_csv('dataset/user_audit_log.csv')
df_act = pd.read_csv('dataset/system_activity.csv')
df_ev = pd.read_csv('dataset/evidence_files.csv')

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

for _, r in df_req.head(15).iterrows():
    cid = r['case_id']
    req_em = r['email'].lower()
    uid = email_to_uid.get(req_em, 'UNKNOWN')
    print(f"\n--- {cid} | {uid} | {req_em} | audit_at: {r['audit_at']} | reported: {r['reported_status']} ---")
    
    # Check system_activity around requested_at to reported_at
    # Look for activities with matching email or user_id or within the time window
    t_start = r['requested_at']
    t_end = r['reported_at']
    m_time = df_act[(df_act['event_time'] >= t_start) & (df_act['event_time'] <= t_end)]
    
    # Check if any activities in m_time match details or if any activities mention user/email
    m_user = df_act[df_act['details'].str.contains(uid, na=False) | df_act['details'].str.contains(req_em, na=False)]
    print(f"  Activities directly mentioning {uid} or {req_em}: {len(m_user)}")
    for _, ar in m_user.iterrows():
        print(f"    {ar['activity_id']} {ar['event_time']} {ar['event_type']} {ar['resource_id']} {ar['reported_result']}")
    
    # Also check if m_time has deletion_worker events
    del_events = m_time[m_time['source_system'] == 'deletion_worker']
    print(f"  Deletion worker events between {t_start} and {t_end}: {len(del_events)}")
    for _, ar in del_events.head(5).iterrows():
        print(f"    {ar['activity_id']} {ar['event_time']} {ar['event_type']} {ar['target_system']} {ar['resource_id']} {ar['reported_result']}")
