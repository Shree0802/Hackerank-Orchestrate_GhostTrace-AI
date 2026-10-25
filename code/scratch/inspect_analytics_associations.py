import pandas as pd
from pathlib import Path
from code.ingestion.csv_loader import CSVDataLoader

loader = CSVDataLoader(Path("dataset"))
df_act = loader.load_system_activity()
df_gold = pd.read_csv("dataset/sample_output.csv")
df_samp = loader.load_sample_deletion_requests()

target_analytics = ['analytics_1895', 'analytics_4566', 'analytics_4574', 'analytics_5335', 'analytics_6077', 'analytics_2265', 'analytics_3264', 'analytics_9447', 'analytics_5589']

for a_id in target_analytics:
    acts = df_act[df_act['resource_id'] == a_id]
    print(f"\n=== {a_id} ===")
    for _, a in acts.iterrows():
        print(f"  {a.event_time} {a.source_system} {a.event_type} {a.reported_result} details={a.details}")
    
    # Check which cases in gold contain this analytics id
    cases_in_gold = []
    import json
    for _, r in df_gold.iterrows():
        steps = json.loads(r['steps_json'])
        if any(s['resource_id'] == a_id for s in steps):
            cases_in_gold.append(r['case_id'])
    print(f"  Appears in Gold Cases: {cases_in_gold}")
