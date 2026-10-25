import json
import pandas as pd
from pathlib import Path
from code.ingestion.csv_loader import CSVDataLoader
from code.evidence.indexer import EvidenceIndexer
from code.ingestion.timestamp_utils import parse_iso_timestamp

loader = CSVDataLoader(Path("dataset"))
df_gold = pd.read_csv("dataset/sample_output.csv")
df_samp = loader.load_sample_deletion_requests()
df_act = loader.load_system_activity()
df_man = loader.load_evidence_manifest()
indexer = EvidenceIndexer(Path("dataset"), df_man, df_act)

for _, row in df_gold.iterrows():
    cid = row['case_id']
    req = df_samp[df_samp['case_id'] == cid].iloc[0]
    t_req = parse_iso_timestamp(req['requested_at'])
    steps = json.loads(row['steps_json'])
    rids = {s['resource_id'] for s in steps}
    for rid in rids:
        # Check where rid appears
        acts = df_act[df_act['resource_id'] == rid]
        obs = indexer.by_resource_id.get(rid, [])
        post_req_obs = [o for o in obs if parse_iso_timestamp(o.get('captured_at')) >= t_req]
        pre_req_obs = [o for o in obs if parse_iso_timestamp(o.get('captured_at')) < t_req]
        
        if len(acts) == 0 and len(post_req_obs) == 0 and len(pre_req_obs) > 0:
            print(f"ONLY PRE-REQ in {cid}: {rid}")
