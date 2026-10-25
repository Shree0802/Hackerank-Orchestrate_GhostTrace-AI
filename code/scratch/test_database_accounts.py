import sqlite3
import pandas as pd
from pathlib import Path

# Let's inspect customer_accounts table from SQL files
# Where are all accounts defined?
df_u = pd.read_csv('dataset/user_identities.csv')
print("Total users in user_identities:", len(df_u))

# Let's check customer_data_primary or customer_accounts across SQL files
sql_files = list(Path('dataset/evidence/databases').glob('*.sql'))
print("SQL files:", len(sql_files))

conn = sqlite3.connect(':memory:')
# Load customer_accounts from one of the earliest database dumps
for f in sorted(sql_files):
    with open(f, 'r', encoding='utf-8') as fp:
        sql = fp.read()
    if 'CREATE TABLE' in sql and 'customer_accounts' in sql:
        print(f"File {f.name} contains customer_accounts")
        # Run statements
        try:
            conn.executescript(sql)
            print(f"Successfully loaded {f.name}")
            break
        except Exception as e:
            print(f"Error loading {f.name}: {e}")

cursor = conn.cursor()
try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print("Tables:", cursor.fetchall())
    cursor.execute("SELECT COUNT(*) FROM customer_accounts;")
    print("customer_accounts count:", cursor.fetchone()[0])
    cursor.execute("SELECT * FROM customer_accounts LIMIT 5;")
    for row in cursor.fetchall():
        print("  ", row)
except Exception as e:
    print("Query error:", e)
