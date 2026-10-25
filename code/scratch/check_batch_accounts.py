import pandas as pd
from pathlib import Path
from code.ingestion.csv_loader import CSVDataLoader
from code.ingestion.timestamp_utils import parse_iso_timestamp

loader = CSVDataLoader(Path('dataset'))
df_req = loader.load_deletion_requests()
df_samp = loader.load_sample_deletion_requests()
df_act = loader.load_system_activity()

worker_acts = df_act[df_act['source_system'] == 'deletion_worker']
acc_acts = worker_acts[worker_acts['resource_id'].str.startswith('account_')]

print("Total account deletion worker acts:", len(acc_acts))
print("Sample requests count:", len(df_samp))

# Group sample requests by reported_at
groups = df_samp.groupby('reported_at')
for rep_at, grp in groups:
    t_rep = parse_iso_timestamp(rep_at)
    matching_accs = []
    for _, a in acc_acts.iterrows():
        t_ev = parse_iso_timestamp(a['event_time'])
        if -5400 <= (t_ev - t_rep).total_seconds() <= 1800:
            matching_accs.append((a['event_time'], a['resource_id'], a['reported_result']))
    print(f"\nReported_at: {rep_at} (Requests: {list(grp['case_id'])})")
    print(f"  Matching accounts in window: {matching_accs}")
