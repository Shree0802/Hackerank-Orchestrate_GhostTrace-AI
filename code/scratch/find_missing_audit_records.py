import glob
import os

targets = [
    'audit_record_6645', '6645',
    'audit_record_5569', '5569',
    'audit_record_3482', '3482',
    'audit_record_7095', '7095',
    'audit_record_6793', '6793'
]

files = glob.glob('dataset/**/*', recursive=True)
for t in targets:
    found = []
    for f in files:
        if os.path.isfile(f) and not f.endswith('sample_output.csv'):
            try:
                with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read().lower()
                    if t.lower() in content:
                        found.append(os.path.basename(f))
            except:
                pass
    print(f"{t}: {found}")
