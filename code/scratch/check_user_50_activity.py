import pandas as pd

df_act = pd.read_csv('dataset/system_activity.csv')
for idx, r in df_act.iterrows():
    text = str(r['resource_id']) + ' ' + str(r['details'])
    if 'user_50' in text or 'mori.ren' in text or '5521' in text or '4013' in text or '037' in text or '5569' in text or '4890' in text or '6645' in text:
        print(f"Row {idx}: {r['activity_id']} | {r['event_time']} | {r['event_type']} | {r['target_system']} | {r['resource_id']} | {r['reported_result']} | {r['details']}")
