import json
from pathlib import Path
import pandas as pd
from collections import defaultdict

from code.ingestion.csv_loader import CSVDataLoader
from code.identity.resolver import IdentityResolver
from code.evidence.indexer import EvidenceIndexer
from code.policy.rules_loader import PolicyRulesLoader
from code.policy.policy_engine import PolicyEngine
from code.agent.remediation_planner import RemediationPlanner
from code.agent.request_classifier import RequestClassifier
from code.output.serializer import OutputSerializer
from code.output.validator import OutputValidator
from code.evaluation.evaluate import Evaluator
from code.audit.state_reconstructor import ResourceState
import code.config as cfg
from code.ingestion.timestamp_utils import is_at_or_before, parse_iso_timestamp

loader = CSVDataLoader(Path('dataset'))
df_identities = loader.load_user_identities()
df_audit_log = loader.load_user_audit_log()
df_manifest = loader.load_evidence_manifest()
df_activity = loader.load_system_activity()
df_rules = loader.load_deletion_rules()
df_samples = loader.load_sample_deletion_requests()
df_sample_out = pd.read_csv('dataset/sample_output.csv')

resolver = IdentityResolver(df_identities, df_audit_log)
indexer = EvidenceIndexer(Path('dataset'), df_manifest, df_activity)
policy_engine = PolicyEngine(PolicyRulesLoader(df_rules))
planner = RemediationPlanner(policy_engine)

print("Starting refined test...")
