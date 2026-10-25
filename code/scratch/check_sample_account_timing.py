import pandas as pd
import json

df_samples = pd.read_csv('dataset/sample_deletion_requests.csv')
df_sample_out = pd.read_csv('dataset/sample_output.csv')
df_act = pd.read_csv('dataset/system_activity.csv')

for _, req in df_samples.iterrows():
    cid = req['case_id']
    t_req = pd.to_datetime(req['requested_at'])
    t_rep = pd.to_datetime(req['reported_at'])
    out_row = df_sample_out[df_sample_out['case_id'] == cid].iloc[0]
    expected_steps = json.loads(out_row['steps_json'])
    acc_steps = [s for s in expected_steps if s['system_id'] == 'account_service']
    if not acc_steps:
        continue
    exp_acc = acc_steps[0]['resource_id']
    
    act_rows = df_act[(df_act['resource_id'] == exp_acc) & (df_act['event_type'] == 'DELETE_RECORD')]
    if len(act_rows) > 0:
        ev_t = pd.to_datetime(act_rows.iloc[0]['event_time'])
        diff_hours = (ev_t - t_rep).total_seconds() / 3600.0
        print(f"{cid} | acc={exp_acc:12} | req={t_req} | rep={t_rep} | ev={ev_t} | diff={diff_hours:+.2f}h")
    else:
        print(f"{cid} | acc={exp_acc:12} | NOT in system_activity!")
