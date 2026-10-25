import pandas as pd
from code.ingestion.csv_loader import CSVDataLoader

loader = CSVDataLoader("dataset")
df_samples = loader.load_sample_deletion_requests()
df_full = loader.load_deletion_requests()
df_all = pd.concat([df_samples, df_full]).drop_duplicates(subset=["case_id"])

df_act = loader.load_system_activity()
worker_acts = df_act[df_act["source_system"] == "deletion_worker"]

status_res_map = {
    "COMPLETE": "SUCCESS",
    "PARTIALLY_COMPLETE": "PARTIAL",
    "NOT_STARTED": "FAILED",
}

for rep_at in ["2026-08-30T12:00:00Z", "2026-09-05T12:00:00Z", "2026-09-06T12:00:00Z"]:
    print(f"=== Batch {rep_at} ===")
    batch_reqs = df_all[df_all["reported_at"] == rep_at]
    for stat in ["COMPLETE", "PARTIALLY_COMPLETE", "NOT_STARTED"]:
        sub_reqs = batch_reqs[batch_reqs["reported_status"] == stat].sort_values(["requested_at", "case_id"])
        if sub_reqs.empty:
            continue
        target_res = status_res_map[stat]
        sub_acts = worker_acts[
            (worker_acts["event_time"] >= rep_at[:10]) & 
            (worker_acts["event_time"] <= rep_at[:10] + "T23:59:59Z") & 
            (worker_acts["reported_result"] == target_res) &
            (worker_acts["resource_id"].str.startswith("account_"))
        ].sort_values("event_time")
        
        req_ids = sub_reqs["case_id"].tolist()
        act_ids = sub_acts["resource_id"].tolist()
        print(f"  Status: {stat} | Reqs ({len(sub_reqs)}): {req_ids} | Acts ({len(sub_acts)}): {act_ids}")
