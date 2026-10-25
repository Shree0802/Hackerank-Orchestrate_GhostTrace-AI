import glob
import os
import re

targets = [
    'account_7566', 'account_3960', 'account_4248', 'account_9797',
    'account_9335', 'account_3677', 'account_4745', 'account_994',
    'account_4092', 'account_5521', 'account_9102', 'account_5037',
    'account_6440', 'account_4990', 'account_410', 'account_5334',
    'account_3136', 'account_5684', 'account_3866', 'account_5482',
    'account_7012', 'account_4163', 'account_4857', 'account_8858'
]

files = glob.glob('dataset/**/*', recursive=True)

found = {}
for t in targets:
    found[t] = []
    for f in files:
        if os.path.isfile(f) and not f.endswith('sample_output.csv'):
            try:
                with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
                    if t in fp.read():
                        found[t].append(f)
            except:
                pass

for t, flist in found.items():
    print(f"{t}: {flist}")
