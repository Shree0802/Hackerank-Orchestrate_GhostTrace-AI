import pandas as pd
import json

df_req = pd.read_csv('dataset/sample_deletion_requests.csv')
df_out = pd.read_csv('dataset/sample_output.csv')
df_act = pd.read_csv('dataset/system_activity.csv')

del_acts = df_act[df_act['source_system'] == 'deletion_worker'].copy()
del_acts['dt'] = pd.to_datetime(del_acts['event_time'])

for _, r in df_req.iterrows():
    cid = r['case_id']
    t_rep = pd.to_datetime(r['reported_at'])
    t_req = pd.to_datetime(r['requested_at'])
    
    out_row = df_out[df_out['case_id'] == cid].iloc[0]
    expected_steps = json.loads(out_row['steps_json'])
    expected_rids = set(s['resource_id'] for s in expected_steps)
    
    # Let's find deletion worker events within [t_rep - 3 hours, t_rep + 3 hours]
    window = del_acts[(del_acts['dt'] >= t_rep - pd.Timedelta(hours=3)) & (del_acts['dt'] <= t_rep + pd.Timedelta(hours=3))]
    
    # Look for account delete event in this window
    acc_events = window[window['target_system'] == 'account_service']
    
    # Print comparison
    print(f"\n{cid} (reported_at: {t_rep}):")
    print(f"  Expected resources: {expected_rids}")
    print(f"  Window del_acts resources: {set(window['resource_id'])}")
    print(f"  Overlap: {expected_rids.intersection(set(window['resource_id']))}")
