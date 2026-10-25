from pathlib import Path
from code.ingestion.csv_loader import CSVDataLoader
from code.identity.resolver import IdentityResolver
from code.audit.state_reconstructor import StateReconstructor
from code.evidence.indexer import EvidenceIndexer

loader = CSVDataLoader(Path('dataset'))
df_id = loader.load_user_identities()
df_aud = loader.load_user_audit_log()
df_man = loader.load_evidence_manifest()
df_act = loader.load_system_activity()
resolver = IdentityResolver(df_id, df_aud)
df_samp = loader.load_sample_deletion_requests()
indexer = EvidenceIndexer(Path('dataset'), df_man, df_act)
reconstructor = StateReconstructor(df_act, df_man, indexer)

for _, req in df_samp.iterrows():
    u = resolver.resolve_email(req['email'])
    states = reconstructor.reconstruct_for_request(req['case_id'], u, req['requested_at'], req['reported_at'], req['audit_at'])
    user_all_idents = {str(x).lower() for x in u.all_identifiers()}
    for s in states:
        obs = indexer.by_resource_id.get(s.resource_id, [])
        known_idents = set()
        for o in obs:
            for idn in o.get('user_identifiers', set()):
                known_idents.add(str(idn).lower())
        if known_idents and known_idents.isdisjoint(user_all_idents):
            print(f"CONFLICT in {req['case_id']}: resource {s.resource_id} has known idents {known_idents} but user is {u.user_id} ({u.all_emails})")
