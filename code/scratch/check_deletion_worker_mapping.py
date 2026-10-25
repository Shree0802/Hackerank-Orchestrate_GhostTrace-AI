import pandas as pd

df_req = pd.read_csv('dataset/sample_deletion_requests.csv')
df_act = pd.read_csv('dataset/system_activity.csv')
del_acts = df_act[df_act['source_system'] == 'deletion_worker']

print(f"Total deletion_worker activities: {len(del_acts)}")
print("Event types for deletion_worker:")
print(del_acts['event_type'].value_counts())
print("\nTarget systems for deletion_worker:")
print(del_acts['target_system'].value_counts())

# Let's inspect primary profile delete events
prof_dels = del_acts[del_acts['target_system'] == 'account_service']
print(f"\nTotal primary profile delete events: {len(prof_dels)}")
print("Sample details:")
for _, r in prof_dels.head(10).iterrows():
    print(r['activity_id'], r['event_time'], r['resource_id'], r['reported_result'], r['details'])
