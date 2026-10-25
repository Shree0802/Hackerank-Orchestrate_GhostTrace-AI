import pandas as pd

df_act = pd.read_csv('dataset/system_activity.csv')
link_rows = df_act[df_act['event_type'] == 'LINK_RESOURCE_IDENTITY']
print(f"LINK_RESOURCE_IDENTITY rows: {len(link_rows)}")
for _, r in link_rows.iterrows():
    print(dict(r))
