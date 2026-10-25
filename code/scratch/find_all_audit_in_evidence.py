import os
import glob
import pandas as pd

targets = [
    'audit_record_2016', 'audit_record_4902', 'audit_record_9394', 'audit_record_2945',
    'audit_record_4816', 'audit_record_987', 'audit_record_1596', 'audit_record_9528',
    'audit_record_1797', 'audit_record_6645', 'audit_record_6793', 'audit_record_5569',
    'audit_record_3737', 'audit_record_3482', 'audit_record_4128', 'audit_record_7095',
    'audit_record_451', 'audit_record_5416', 'audit_record_3830', 'audit_record_9265',
    'audit_record_3954', 'audit_record_1707', 'audit_record_6909', 'audit_record_7068'
]

files = glob.glob('dataset/evidence/**/*', recursive=True)
for t in targets:
    found = []
    for f in files:
        if os.path.isfile(f):
            try:
                with open(f, 'rb') as fp:
                    if t.encode() in fp.read():
                        found.append(os.path.basename(f))
            except:
                pass
    print(f"{t}: {found}")
