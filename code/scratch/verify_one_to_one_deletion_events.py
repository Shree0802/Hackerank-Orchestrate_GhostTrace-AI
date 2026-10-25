import pandas as pd

df_all_req = pd.concat([
    pd.read_csv('dataset/sample_deletion_requests.csv'),
    pd.read_csv('dataset/deletion_requests.csv')
], ignore_index=True)

df_act = pd.read_csv('dataset/system_activity.csv')
prof_dels = df_act[(df_act['source_system'] == 'deletion_worker') & (df_act['target_system'] == 'account_service') & (df_act['event_type'] == 'DELETE_RECORD')].copy()

# Sort by event_time
prof_dels['dt'] = pd.to_datetime(prof_dels['event_time'])
prof_dels = prof_dels.sort_values('dt').reset_index(drop=True)

print(f"Total requests: {len(df_all_req)}")
print(f"Total account delete events: {len(prof_dels)}")

# For each request, check if there is an account delete event close to reported_at or requested_at
matched = 0
unmatched = []

for _, r in df_all_req.iterrows():
    cid = r['case_id']
    t_req = pd.to_datetime(r['requested_at'])
    t_rep = pd.to_datetime(r['reported_at'])
    st = r['reported_status']
    
    # check candidates between requested_at and reported_at + 15 mins
    candidates = prof_dels[(prof_dels['dt'] >= t_req - pd.Timedelta(hours=1)) & (prof_dels['dt'] <= t_rep + pd.Timedelta(hours=1))]
    if len(candidates) > 0:
        matched += 1
    else:
        unmatched.append((cid, st, r['request_text'][:60]))

print(f"Matched requests to account delete events in window: {matched}")
print(f"Unmatched: {len(unmatched)}")
for u in unmatched[:15]:
    print(" ", u)
