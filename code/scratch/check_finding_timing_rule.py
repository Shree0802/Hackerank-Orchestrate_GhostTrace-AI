import pandas as pd
import json

df_samples = pd.read_csv('dataset/sample_deletion_requests.csv')
df_sample_out = pd.read_csv('dataset/sample_output.csv')
df_ev = pd.read_csv('dataset/evidence_files.csv')
ev_times = {r['file_id']: r['captured_at'] for _, r in df_ev.iterrows()}

violations_before_req = 0

for _, req in df_samples.iterrows():
    cid = req['case_id']
    t_req = req['requested_at']
    steps = json.loads(df_sample_out[df_sample_out['case_id'] == cid]['steps_json'].iloc[0])
    for s in steps:
        if s['phase'] == 'FINDING':
            eid = s['evidence_id']
            cap_at = ev_times.get(eid)
            if cap_at and cap_at < t_req:
                print(f"Finding before requested_at in {cid}: {s['resource_id']} ev={eid} cap={cap_at} < req={t_req}")
                violations_before_req += 1

print("Total findings cited before requested_at:", violations_before_req)
