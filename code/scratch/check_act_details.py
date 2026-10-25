import pandas as pd

df_act = pd.read_csv('dataset/system_activity.csv')

check_ids = ['account_5521', 'account_5037', 'account_4990', 'account_7012', 'account_4163', 'account_4857', 'account_8858']
for aid in check_ids:
    print(f"\nActivity for {aid}:")
    m = df_act[df_act['resource_id'] == aid]
    for _, r in m.iterrows():
        print(f"  {r['activity_id']} | {r['event_time']} | {r['event_type']} | {r['source_system']} -> {r['target_system']} | {r['reported_result']} | {r['details']}")
