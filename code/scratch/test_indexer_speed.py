import time
import os
import glob
import json
import sqlite3
import re
import pandas as pd

start_time = time.time()

df_ev = pd.read_csv('dataset/evidence_files.csv')
print(f"Indexing {len(df_ev)} evidence files...")

parsed_counts = 0
for _, r in df_ev.iterrows():
    p = os.path.join('dataset', r['file_path'])
    if not os.path.exists(p):
        continue
    parsed_counts += 1
    if p.endswith('.json'):
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
    elif p.endswith('.sql'):
        with open(p, 'r', encoding='utf-8') as f:
            text = f.read()
    elif p.endswith('.log') or p.endswith('.txt'):
        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    elif p.endswith('.pdf'):
        import fitz
        doc = fitz.open(p)
        text = "\n".join([page.get_text() for page in doc])

elapsed = time.time() - start_time
print(f"Read and parsed {parsed_counts} files in {elapsed:.2f} seconds!")
