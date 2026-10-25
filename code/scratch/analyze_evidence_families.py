import pandas as pd
import re
from collections import defaultdict

df_ev = pd.read_csv('dataset/evidence_files.csv')
families = defaultdict(list)

for _, r in df_ev.iterrows():
    # clean filename to find pattern
    fname = r['file_path'].split('/')[-1]
    # replace dates/timestamps with *
    pat = re.sub(r'\d{8}(_\d{6})?', '*', fname)
    families[pat].append((r['file_id'], r['captured_at'], r['file_path'], r['origin']))

print(f"Total evidence files: {len(df_ev)}")
print(f"Total distinct file families: {len(families)}")
for pat, items in sorted(families.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\nFamily: {pat} ({len(items)} files)")
    for fid, cap, p, orig in items[:3]:
        print(f"  {fid} | {cap} | {p}")
    if len(items) > 3:
        print(f"  ... and {len(items)-3} more (latest: {items[-1][0]} at {items[-1][1]})")
