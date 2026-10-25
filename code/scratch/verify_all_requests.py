import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

df_req = pd.read_csv('dataset/deletion_requests.csv')

non_deletion_cids = []
for idx, r in df_req.iterrows():
    text = r['request_text'].lower()
    # Indications of non-deletion:
    # "leave the account active", "not asking for deletion", "keep the account as it is",
    # "do not close the account", "without removing", "marketing lists only",
    # "information request, not a request to erase", "leave my profile", "continue using the service",
    # "don't delete or change anything"
    is_non_del = (
        'leave the account active' in text or
        'not asking for deletion' in text or
        'keep the account' in text or
        'do not close' in text or
        'without removing' in text or
        'marketing lists only' in text or
        'information request, not a request to erase' in text or
        'leave my profile' in text or
        'continue using the service' in text or
        'don\'t delete' in text or
        'do not delete' in text
    )
    if is_non_del:
        non_deletion_cids.append((r['case_id'], r['request_text']))

print(f"Total non-deletion cases identified: {len(non_deletion_cids)}")
for cid, txt in non_deletion_cids:
    print(f"  {cid}: {txt}")
