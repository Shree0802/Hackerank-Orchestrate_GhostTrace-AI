import pandas as pd
from pathlib import Path
from code.ingestion.csv_loader import CSVDataLoader
from code.ingestion.timestamp_utils import parse_iso_timestamp

loader = CSVDataLoader(Path('dataset'))
df_samp = loader.load_sample_deletion_requests()
df_act = loader.load_system_activity()
df_gold = pd.read_csv("dataset/sample_output.csv")

worker_acts = df_act[df_act['source_system'] == 'deletion_worker']
acc_acts = worker_acts[worker_acts['resource_id'].str.startswith('account_')]

status_map = {
    'COMPLETE': 'SUCCESS',
    'PARTIALLY_COMPLETE': 'PARTIAL',
    'NOT_STARTED': 'FAILED'
}

for _, req in df_samp.iterrows():
    cid = req['case_id']
    rep_at = req['reported_at']
    rep_stat = req['reported_status']
    exp_res = status_map.get(rep_stat)
    
    # Gold account
    g_row = df_gold[df_gold['case_id'] == cid].iloc[0]
    import json
    g_steps = json.loads(g_row['steps_json'])
    g_accs = [s['resource_id'] for s in g_steps if s['resource_id'].startswith('account_')]
    
    t_rep = parse_iso_timestamp(rep_at)
    matching_accs = []
    for _, a in acc_acts.iterrows():
        t_ev = parse_iso_timestamp(a['event_time'])
        if -5400 <= (t_ev - t_rep).total_seconds() <= 1800:
            matching_accs.append((a['event_time'], a['resource_id'], a['reported_result']))
            
    filtered_by_status = [a for a in matching_accs if a[2] == exp_res]
    print(f"{cid} (rep_stat={rep_stat} -> {exp_res}): Gold={g_accs}")
    print(f"   In window: {matching_accs}")
    print(f"   Matching status: {filtered_by_status}")
