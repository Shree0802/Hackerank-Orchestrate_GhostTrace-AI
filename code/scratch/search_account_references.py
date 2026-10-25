import os, re

target_rids = ['account_3866', 'account_5482', 'account_7012', 'account_4857', 'account_8858', 'account_3960']

for root, _, files in os.walk('dataset'):
    for f in files:
        fpath = os.path.join(root, f)
        if f.endswith(('.csv', '.json', '.txt', '.log', '.sql')):
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
                    for rid in target_rids:
                        if rid in content:
                            matches = [line for line in content.splitlines() if rid in line]
                            print(f"{f}: {rid} -> {len(matches)} matches")
                            for m in matches[:3]:
                                print(f"    {m[:120]}")
            except Exception as e:
                pass
