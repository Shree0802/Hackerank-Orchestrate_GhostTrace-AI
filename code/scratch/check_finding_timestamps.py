import json
import pandas as pd
from pathlib import Path
from code.ingestion.csv_loader import CSVDataLoader
from code.ingestion.timestamp_utils import parse_iso_timestamp

loader = CSVDataLoader(Path('dataset'))
df_gold = pd.read_csv("dataset/sample_output.csv")
df_samp = loader.load_sample_deletion_requests()
df_man = loader.load_evidence_manifest()
ev_times = dict(zip(df_man['file_id'], df_man['captured_at']))

violations_before_req = 0
total_findings = 0
for _, row in df_gold.iterrows():
    cid = row['case_id']
    req = df_samp[df_samp['case_id'] == cid].iloc[0]
    t_req = parse_iso_timestamp(req['requested_at'])
    steps = json.loads(row['steps_json'])
    for s in steps:
        if s['phase'] == 'FINDING':
            total_findings += 1
            ev_id = s.get('evidence_id')
            cap_at = ev_times.get(ev_id)
            if cap_at:
                t_cap = parse_iso_timestamp(cap_at)
                if t_cap < t_req:
                    print(f"Finding before req in {cid}: {s['resource_id']} ev={ev_id} cap={cap_at} req={req['requested_at']}")
                    violations_before_req += 1

print(f"Total findings in gold: {total_findings}, Findings before requested_at: {violations_before_req}")
