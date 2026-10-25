import pandas as pd
import json

df_samples = pd.read_csv('dataset/sample_deletion_requests.csv')
df_sample_out = pd.read_csv('dataset/sample_output.csv')
df_u = pd.read_csv('dataset/user_identities.csv')
df_a = pd.read_csv('dataset/user_audit_log.csv')
df_act = pd.read_csv('dataset/system_activity.csv')

email_to_uid = {r['email'].lower(): r['user_id'] for _, r in df_u.iterrows()}
for _, r in df_a.iterrows():
    if r['field_name'] == 'email':
        email_to_uid[str(r['old_value']).lower()] = r['user_id']
        email_to_uid[str(r['new_value']).lower()] = r['user_id']

for _, req in df_samples.iterrows():
    cid = req['case_id']
    em = req['email'].lower()
    uid = email_to_uid[em]
    t_rep = pd.to_datetime(req['reported_at'])
    out_row = df_sample_out[df_sample_out['case_id'] == cid].iloc[0]
    expected_steps = json.loads(out_row['steps_json'])
    acc_steps = [s for s in expected_steps if s['system_id'] == 'account_service']
    exp_acc = acc_steps[0]['resource_id'] if acc_steps else "NONE"
    
    # Check where exp_acc appears
    in_act = len(df_act[df_act['resource_id'] == exp_acc])
    user_num = uid.replace('user_', '')
    convention_acc = f"account_{int(user_num):03d}"
    
    print(f"{cid} | {uid} | exp_acc={exp_acc:12} | convention={convention_acc:12} | in_act={in_act}")
