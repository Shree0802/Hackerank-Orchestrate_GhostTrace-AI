import pandas as pd
import json
import os

df_ev = pd.read_csv('dataset/evidence_files.csv')
df_ev['captured_at_dt'] = pd.to_datetime(df_ev['captured_at'])
df_ev = df_ev.sort_values('captured_at_dt')
print("Chronological evidence files:")
for _, r in df_ev.iterrows():
    print(f"{r['file_id']:<12} {r['captured_at']}  {r['file_path']:<65}  {r['origin']}")
