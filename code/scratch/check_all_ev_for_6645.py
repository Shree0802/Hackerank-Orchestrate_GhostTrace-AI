import pandas as pd
import glob

df_ev = pd.read_csv('dataset/evidence_files.csv')
for _, r in df_ev.iterrows():
    p = 'dataset/' + r['file_path']
    try:
        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if '6645' in content:
                print(f"Found 6645 in {r['file_id']} ({r['file_path']})")
            if '5569' in content:
                print(f"Found 5569 in {r['file_id']} ({r['file_path']})")
    except Exception as e:
        pass
