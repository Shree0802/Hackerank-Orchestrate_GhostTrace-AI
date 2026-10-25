import pandas as pd
import json

df_gold = pd.read_csv('dataset/sample_output.csv')
for _, row in df_gold.iterrows():
    steps = json.loads(row['steps_json'])
    audits = [s['resource_id'] for s in steps if s['resource_id'].startswith('audit_record_')]
    if audits:
        print(f"{row['case_id']}: {audits}")
