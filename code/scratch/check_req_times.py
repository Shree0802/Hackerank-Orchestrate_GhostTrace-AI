import pandas as pd

df_req = pd.read_csv('dataset/sample_deletion_requests.csv')
for cid in ['case_18', 'case_20', 'case_22', 'case_29', 'case_30', 'case_31', 'case_32']:
    row = df_req[df_req['case_id'] == cid].iloc[0]
    print(f"{cid} | requested: {row['requested_at']} | reported: {row['reported_at']} | reported_status: {row['reported_status']}")
