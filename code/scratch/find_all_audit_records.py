import os
from pathlib import Path

target_auds = [
    'audit_record_2016', 'audit_record_9394', 'audit_record_2945', 'audit_record_4816',
    'audit_record_987', 'audit_record_1596', 'audit_record_9528', 'audit_record_6793',
    'audit_record_3482', 'audit_record_4128', 'audit_record_7095', 'audit_record_3954',
    'audit_record_1707', 'audit_record_6909', 'audit_record_7068'
]

found = {}
for root, _, files in os.walk('dataset'):
    for f in files:
        fpath = os.path.join(root, f)
        if f.endswith(('.csv', '.json', '.sql', '.log', '.txt')):
            try:
                c = open(fpath, errors='ignore').read()
                for a in target_auds:
                    if a in c:
                        if a not in found:
                            found[a] = []
                        found[a].append(f)
            except:
                pass

for a in target_auds:
    print(f"{a}: {found.get(a, 'NOT FOUND')}")
