import pandas as pd

df_req = pd.read_csv('dataset/deletion_requests.csv')
df_sample = pd.read_csv('dataset/sample_deletion_requests.csv')
df_sample_out = pd.read_csv('dataset/sample_output.csv')

print("Sample requests deletion_status distribution:")
print(df_sample_out['deletion_status'].value_counts())

# Check sample request texts for any non-deletion requests
for _, r in df_sample.iterrows():
    cid = r['case_id']
    st = df_sample_out[df_sample_out['case_id'] == cid]['deletion_status'].iloc[0]
    if st == 'NOT_APPLICABLE':
        print(f"Sample NOT_APPLICABLE: {cid} - {r['request_text']}")

# Check words in deletion_requests.csv
non_del_keywords = ['access', 'export', 'download', 'copy of my data', 'unsubscribe', 'opt out', 'newsletter', 'correct', 'update my email', 'change my phone']
print("\nChecking for non-deletion keywords in deletion_requests.csv:")
for idx, r in df_req.iterrows():
    text = r['request_text'].lower()
    for kw in ['access', 'export', 'download', 'update', 'marketing', 'newsletter', 'opt-out', 'opt out', 'rectif']:
        if kw in text and not any(del_kw in text for del_kw in ['delet', 'eras', 'close', 'remov', 'supprim', 'eliminar']):
            print(f"Potential non-deletion: {r['case_id']} | {r['request_text'][:120]}")
            break
