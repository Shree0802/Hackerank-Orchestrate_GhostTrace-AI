import pandas as pd
import json

df_gold = pd.read_csv('dataset/sample_output.csv').set_index('case_id')
cases = ['case_03', 'case_04', 'case_07', 'case_11', 'case_13', 'case_17', 'case_18', 'case_19', 'case_20', 'case_23', 'case_24', 'case_25', 'case_26', 'case_27', 'case_28', 'case_29', 'case_32']

for cid in cases:
    print(f"=== Gold for {cid} ===")
    steps = json.loads(df_gold.loc[cid, 'steps_json'])
    for s in steps:
        print(f"  {s['step_no']}. {s['phase']} | {s['operation']} | {s['resource_id']} | {s['state']} | {s['evidence_id']}")
