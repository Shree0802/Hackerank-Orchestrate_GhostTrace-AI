import json
import pandas as pd
from pathlib import Path
from code.ingestion.csv_loader import CSVDataLoader

loader = CSVDataLoader(Path('dataset'))
df_gold = pd.read_csv("dataset/sample_output.csv")
df_act = loader.load_system_activity()

worker_acts = df_act[df_act['source_system'] == 'deletion_worker']
act_by_res = {}
for _, a in worker_acts.iterrows():
    rid = a['resource_id']
    if rid not in act_by_res:
        act_by_res[rid] = []
    act_by_res[rid].append(a)

matches = 0
total_rems = 0
for _, row in df_gold.iterrows():
    cid = row['case_id']
    steps = json.loads(row['steps_json'])
    rems = [s for s in steps if s['phase'] == 'REMEDIATION']
    for r in rems:
        total_rems += 1
        rid = r['resource_id']
        op = r['operation']
        acts = act_by_res.get(rid, [])
        worker_ops = [a['event_type'] for a in acts]
        if op in worker_ops:
            matches += 1
        else:
            print(f"Mismatch in {cid}: {rid} gold_rem_op={op} worker_ops={worker_ops}")

print(f"Total remediations in gold: {total_rems}, Matched worker event_type: {matches}")
