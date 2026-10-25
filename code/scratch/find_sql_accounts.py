from pathlib import Path
import re

account_to_user = {}

for f in Path('dataset/evidence').rglob('*.sql'):
    c = open(f, errors='ignore').read()
    for line in c.splitlines():
        if 'account_' in line and ('user_' in line or '@' in line):
            acc_match = re.search(r'(account_\d+)', line)
            user_match = re.search(r'(user_\d+)', line)
            email_match = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', line)
            if acc_match and (user_match or email_match):
                acc = acc_match.group(1)
                u = user_match.group(1) if user_match else None
                em = email_match.group(1) if email_match else None
                account_to_user[acc] = (u, em)

print(f"Total account mappings found in SQL: {len(account_to_user)}")
for k, v in list(account_to_user.items())[:15]:
    print(k, v)
