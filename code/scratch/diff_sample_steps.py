import json
import pandas as pd

df_gold = pd.read_csv("dataset/sample_output.csv")
df_pred = pd.read_csv("code/scratch/sample_predictions.csv")

for _, g_row in df_gold.iterrows():
    cid = g_row['case_id']
    p_row = df_pred[df_pred['case_id'] == cid].iloc[0]
    g_steps = json.loads(g_row['steps_json'])
    p_steps = json.loads(p_row['steps_json'])
    
    g_set = {(s['phase'], s['system_id'], s['resource_id'], s['operation'], s['state'], s.get('evidence_id', '')) for s in g_steps}
    p_set = {(s['phase'], s['system_id'], s['resource_id'], s['operation'], s['state'], s.get('evidence_id', '')) for s in p_steps}
    
    missing_in_pred = g_set - p_set
    extra_in_pred = p_set - g_set
    
    if missing_in_pred or extra_in_pred:
        print(f"=== {cid} ===")
        if missing_in_pred:
            print("  MISSING IN PRED (Gold has, Pred doesn't):")
            for m in missing_in_pred:
                print("   ", m)
        if extra_in_pred:
            print("  EXTRA IN PRED (Pred has, Gold doesn't):")
            for e in extra_in_pred:
                print("   ", e)
