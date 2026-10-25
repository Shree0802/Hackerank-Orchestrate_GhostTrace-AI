from pathlib import Path
from code.ingestion.csv_loader import CSVDataLoader

loader = CSVDataLoader(Path("dataset"))
df_req = loader.load_deletion_requests()
df_samp = loader.load_sample_deletion_requests()
df_act = loader.load_system_activity()

for acc in ['account_7015', 'account_410', 'account_9155']:
    acts = df_act[df_act['resource_id'] == acc]
    print(f"\n=== {acc} ===")
    for _, a in acts.iterrows():
        print(f"  {a.event_time} {a.source_system} {a.event_type} {a.reported_result} details={a.details}")
    # Search in all evidence files
    for f in Path("dataset/evidence").rglob("*"):
        if f.is_file():
            try:
                c = open(f, errors='ignore').read()
                if acc in c:
                    print(f"  In evidence: {f.name}")
            except:
                pass
