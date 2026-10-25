import os

targets = [f'account_00{i}' for i in range(1, 10)] + ['account_010']
for t in targets:
    found = []
    for root, dirs, files in os.walk('dataset'):
        if 'sample_output' in root or 'sample_output' in str(files):
            continue
        for f in files:
            p = os.path.join(root, f)
            try:
                with open(p, 'rb') as fp:
                    if t.encode() in fp.read():
                        found.append(f)
            except:
                pass
    print(f"{t}: {found}")
