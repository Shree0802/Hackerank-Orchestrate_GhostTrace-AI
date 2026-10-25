import pandas as pd
import json

df_samples = pd.read_csv('dataset/sample_deletion_requests.csv')
df_sample_out = pd.read_csv('dataset/sample_output.csv')
df_ev = pd.read_csv('dataset/evidence_files.csv')
ev_map = {r['file_id']: (r['file_path'], r['captured_at']) for _, r in df_ev.iterrows()}

for _, req in df_samples.iterrows():
    cid = req['case_id']
    t_aud = req['audit_at']
    st = df_sample_out[df_sample_out['case_id'] == cid]['deletion_status'].iloc[0]
    steps = json.loads(df_sample_out[df_sample_out['case_id'] == cid]['steps_json'].iloc[0])
    
    print(f"\n{cid} [{st}] audit_at={t_aud}:")
    for s in steps:
        eid = s['evidence_id']
        ev_info = ev_map.get(eid, ("NONE", "NONE"))
        print(f"  {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | ev={eid} ({ev_info[0]} @ {ev_info[1]})")
