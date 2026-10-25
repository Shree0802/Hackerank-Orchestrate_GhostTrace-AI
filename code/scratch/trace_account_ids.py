import pandas as pd

df_act = pd.read_csv('dataset/system_activity.csv')

# Check all activities mentioning account_001, account_002, etc.
for i in [1, 2, 4, 5, 6, 7, 8, 10]:
    acc = f"account_{i:03d}"
    m = df_act[df_act['resource_id'] == acc]
    print(f"\nActivities for {acc}:")
    for _, r in m.iterrows():
        print(f"  {r['activity_id']} | {r['event_time']} | {r['event_type']} | {r['source_system']} -> {r['target_system']} | {r['reported_result']} | {r['details']}")
