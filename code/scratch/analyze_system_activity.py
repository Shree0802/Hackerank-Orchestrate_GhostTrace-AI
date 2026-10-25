import pandas as pd
import re

df_act = pd.read_csv('dataset/system_activity.csv')
print(f"Total system_activity rows: {len(df_act)}")
print("Event types:", df_act['event_type'].value_counts().to_dict())
print("Source systems:", df_act['source_system'].value_counts().to_dict())
print("Target systems:", df_act['target_system'].value_counts().to_dict())
print("Reported results:", df_act['reported_result'].value_counts().to_dict())

# How do resources connect to users or emails in system_activity?
# Check details column for patterns:
users_found = df_act['details'].apply(lambda x: re.findall(r'user_\d+', str(x)))
emails_found = df_act['details'].apply(lambda x: re.findall(r'[\w\.-]+@[\w\.-]+', str(x)))
print(f"Rows with user_id in details: {users_found.apply(bool).sum()}")
print(f"Rows with email in details: {emails_found.apply(bool).sum()}")

# What about resource_id prefixes?
res_prefixes = df_act['resource_id'].apply(lambda x: str(x).split('_')[0] if pd.notna(x) else 'none')
print("Resource prefixes in system_activity:", res_prefixes.value_counts().to_dict())
