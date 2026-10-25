import pandas as pd
from datetime import datetime

df_samples = pd.read_csv('dataset/sample_deletion_requests.csv')
df_requests = pd.read_csv('dataset/deletion_requests.csv')
df_act = pd.read_csv('dataset/system_activity.csv')

# Filter deletion worker account delete events
del_events = df_act[(df_act['source_system'] == 'deletion_worker') & (df_act['target_system'] == 'account_service') & (df_act['event_type'] == 'DELETE_RECORD')].copy()
del_events['t'] = pd.to_datetime(del_events['event_time'])
del_events = del_events.sort_values('t')

print(f"Total account DELETE_RECORD events by deletion_worker: {len(del_events)}")

# Check matching for samples
sample_matches = 0
for _, r in df_samples.iterrows():
    t_req = pd.to_datetime(r['requested_at'])
    t_rep = pd.to_datetime(r['reported_at'])
    # Event occurs around [t_req - 1h, t_rep + 1h]
    matches = del_events[(del_events['t'] >= t_req - pd.Timedelta(hours=1)) & (del_events['t'] <= t_rep + pd.Timedelta(hours=1))]
    if len(matches) == 1:
        sample_matches += 1
    else:
        print(f"Sample {r['case_id']}: {len(matches)} matches in window [{t_req} .. {t_rep}]")

print(f"Sample requests matching exactly 1 account deletion event: {sample_matches}/{len(df_samples)}")
