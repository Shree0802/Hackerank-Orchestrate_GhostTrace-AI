import pandas as pd
import re

df_req = pd.read_csv('dataset/deletion_requests.csv')
df_u = pd.read_csv('dataset/user_identities.csv')
df_a = pd.read_csv('dataset/user_audit_log.csv')

print(f"Total requests in deletion_requests.csv: {len(df_req)}")
print("Reported status distribution:")
print(df_req['reported_status'].value_counts())

# Build mapping of email -> user_id
current_emails = {r['email'].lower(): r['user_id'] for _, r in df_u.iterrows()}
hist_emails = {}
for _, r in df_a.iterrows():
    if r['field_name'] == 'email':
        hist_emails[str(r['old_value']).lower()] = r['user_id']
        hist_emails[str(r['new_value']).lower()] = r['user_id']

matched_current = 0
matched_hist = 0
unmatched = 0

for _, r in df_req.iterrows():
    em = r['email'].lower()
    if em in current_emails:
        matched_current += 1
    elif em in hist_emails:
        matched_hist += 1
    else:
        unmatched += 1

print(f"\nIdentity resolution:")
print(f"  Matched current email: {matched_current}")
print(f"  Matched historical email: {matched_hist}")
print(f"  Unmatched: {unmatched}")

# Check request text categories: deletion vs non-deletion
print("\nSample request texts:")
for i, r in df_req.head(10).iterrows():
    print(f"[{r['case_id']}] ({r['reported_status']}) {r['request_text'][:100]}...")
