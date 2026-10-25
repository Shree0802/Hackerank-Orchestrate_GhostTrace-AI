import pandas as pd
from datetime import datetime

df_reqs = pd.read_csv('dataset/deletion_requests.csv')
df_act = pd.read_csv('dataset/system_activity.csv')
df_u = pd.read_csv('dataset/user_identities.csv')
df_a = pd.read_csv('dataset/user_audit_log.csv')

# Build mapping of emails
email_to_uid = {r['email'].lower(): r['user_id'] for _, r in df_u.iterrows()}
for _, r in df_a.iterrows():
    if r['field_name'] == 'email':
        email_to_uid[str(r['old_value']).lower()] = r['user_id']
        email_to_uid[str(r['new_value']).lower()] = r['user_id']

del_acts = df_act[(df_act['source_system'] == 'deletion_worker') & (df_act['target_system'] == 'account_service') & (df_act['event_type'] == 'DELETE_RECORD')].copy()
del_acts['dt'] = pd.to_datetime(del_acts['event_time'])

matched_count = 0
unmatched = []

for _, r in df_reqs.iterrows():
    cid = r['case_id']
    t_rep = pd.to_datetime(r['reported_at'])
    t_req = pd.to_datetime(r['requested_at'])
    
    # Check deletion worker account delete events in [t_rep - 4 hours, t_rep + 4 hours]
    win = del_acts[(del_acts['dt'] >= t_rep - pd.Timedelta(hours=4)) & (del_acts['dt'] <= t_rep + pd.Timedelta(hours=4))]
    if len(win) >= 1:
        matched_count += 1
    else:
        unmatched.append((cid, r['email'], str(t_req), str(t_rep)))

print(f"Matched {matched_count}/{len(df_reqs)} deletion requests to an account deletion event in [reported_at +- 4h]")
print(f"Unmatched: {len(unmatched)}")
if unmatched[:10]:
    print("First few unmatched:", unmatched[:10])
