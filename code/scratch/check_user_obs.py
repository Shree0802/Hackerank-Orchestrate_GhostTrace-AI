import sys
from pathlib import Path
from code.ingestion.csv_loader import CSVDataLoader
from code.identity.resolver import IdentityResolver
from code.evidence.indexer import EvidenceIndexer

dataset_dir = Path('dataset')
loader = CSVDataLoader(dataset_dir)
df_manifest = loader.load_evidence_manifest()
df_activity = loader.load_system_activity()
df_identities = loader.load_user_identities()
df_audit_log = loader.load_user_audit_log()

indexer = EvidenceIndexer(dataset_dir, df_manifest, df_activity)
resolver = IdentityResolver(df_identities, df_audit_log)

user_43 = resolver.resolve_by_email('alison.rodriguez.1983@example.com')
print('User 43 id:', user_43.user_id)
obs_43 = indexer.find_observations_for_user(user_43)
for o in obs_43:
    print('  ', o)
