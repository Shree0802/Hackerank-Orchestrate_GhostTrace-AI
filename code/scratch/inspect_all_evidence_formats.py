import json
import sqlite3
import re
import os
import glob

def check_file(path):
    print("="*60)
    print("FILE:", path)
    if path.endswith('.json'):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            print("Dict keys:", list(data.keys())[:10])
            for k in list(data.keys())[:3]:
                val = data[k]
                if isinstance(val, list):
                    print(f"  {k} (list of {len(val)}): sample {val[0] if val else None}")
                else:
                    print(f"  {k}: {str(val)[:100]}")
        elif isinstance(data, list):
            print(f"List of {len(data)} items. Sample: {data[0] if data else None}")
    elif path.endswith('.sql'):
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        tables = re.findall(r'CREATE TABLE (\w+)', text)
        print("SQL tables:", tables)
        for t in tables[:3]:
            inserts = re.findall(rf'INSERT INTO "?{t}"? VALUES\((.*?)\);', text)
            print(f"  Table {t}: {len(inserts)} rows. Sample insert: {inserts[0] if inserts else None}")
    elif path.endswith('.log'):
        with open(path, 'r', encoding='utf-8') as f:
            lines = [f.readline().strip() for _ in range(5)]
        print("Log sample lines:")
        for l in lines:
            if l:
                print(" ", l[:120])
    elif path.endswith('.txt'):
        with open(path, 'r', encoding='utf-8') as f:
            lines = [f.readline().strip() for _ in range(5)]
        print("Txt sample lines:")
        for l in lines:
            if l:
                print(" ", l[:120])

# Inspect one of each format
samples = [
    'dataset/evidence/records/service_resource_export_20260915_114455.json',
    'dataset/evidence/records/customer_data_snapshot_bundle_20260915.json',
    'dataset/evidence/records/customer_analytics_report_20260907.json',
    'dataset/evidence/records/customer_export_jobs_20260914.json',
    'dataset/evidence/records/connector_configurations_20260812.json',
    'dataset/evidence/records/security_audit_ledger_20261001.json',
    'dataset/evidence/records/customer_export_manifest_20260409.json',
    'dataset/evidence/databases/customer_data_inventory_20260916.sql',
    'dataset/evidence/databases/customer_data_read_replica_20260921.sql',
    'dataset/evidence/databases/customer_accounts_failover_replica_20260902.sql',
    'dataset/evidence/databases/customer_search_primary_20260910.sql',
    'dataset/evidence/databases/customer_data_failover_replica_20260920.sql',
    'dataset/evidence/logs/resource_lookup_trace_20260926_103856.log',
    'dataset/evidence/logs/service_events_ap_south_20260915.log',
    'dataset/evidence/logs/support_replica.log',
    'dataset/evidence/logs/search_index_diagnostic_20260906.log'
]

for s in samples:
    if os.path.exists(s):
        check_file(s)
