import pandas as pd
import json

df_samples = pd.read_csv('dataset/sample_deletion_requests.csv')
df_sample_out = pd.read_csv('dataset/sample_output.csv')
df_act = pd.read_csv('dataset/system_activity.csv')

dw_acts = df_act[df_act['source_system'] == 'deletion_worker'].copy()
dw_acts['dt'] = pd.to_datetime(dw_acts['event_time'])

for _, req in df_samples.iterrows():
    cid = req['case_id']
    t_rep = pd.to_datetime(req['reported_at'])
    out_row = df_sample_out[df_sample_out['case_id'] == cid].iloc[0]
    expected_steps = json.loads(out_row['steps_json'])
    expected_rids = set(s['resource_id'] for s in expected_steps)
    
    # Check deletion worker events within [t_rep - 30 minutes, t_rep + 30 minutes]
    nearby = dw_acts[(dw_acts['dt'] >= t_rep - pd.Timedelta(minutes=30)) & (dw_acts['dt'] <= t_rep + pd.Timedelta(minutes=30))]
    nearby_rids = set(nearby['resource_id'].dropna())
    
    overlap = expected_rids.intersection(nearby_rids)
    print(f"{cid} (rep: {t_rep}): expected {len(expected_rids)} rids: {expected_rids}")
    print(f"   Nearby dw rids: {nearby_rids}")
    print(f"   Overlap: {overlap}")
