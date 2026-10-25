import pandas as pd
import json

df_req = pd.read_csv('dataset/sample_deletion_requests.csv')
df_out = pd.read_csv('dataset/sample_output.csv')
df_ev = pd.read_csv('dataset/evidence_files.csv')
df_ev['dt'] = pd.to_datetime(df_ev['captured_at'])

for _, r in df_req.iterrows():
    cid = r['case_id']
    t_aud = pd.to_datetime(r['audit_at'])
    out_row = df_out[df_out['case_id'] == cid].iloc[0]
    steps = json.loads(out_row['steps_json'])
    
    # What are the evidence files captured <= t_aud?
    valid_ev = df_ev[df_ev['dt'] <= t_aud].sort_values('dt', ascending=False)
    
    cited_in_steps = {s['resource_id']: s['evidence_id'] for s in steps if s['evidence_id']}
    if cited_in_steps:
        print(f"\n{cid} (audit_at: {t_aud}):")
        print(f"  Steps cited: {cited_in_steps}")
        print(f"  Top 3 closest evidence files <= audit_at:")
        for _, ev_row in valid_ev.head(3).iterrows():
            print(f"    {ev_row['file_id']} ({ev_row['captured_at']}): {ev_row['file_path']}")
