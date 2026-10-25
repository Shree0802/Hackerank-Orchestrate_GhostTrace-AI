"""End-to-end integration tests verifying the full deletion audit pipeline."""

import unittest
from pathlib import Path
from code.ingestion.csv_loader import CSVDataLoader
from code.identity.resolver import IdentityResolver
from code.evidence.indexer import EvidenceIndexer
from code.policy.rules_loader import PolicyRulesLoader
from code.policy.policy_engine import PolicyEngine
from code.audit.state_reconstructor import StateReconstructor
from code.agent.remediation_planner import RemediationPlanner
from code.agent.decision_engine import DeletionDecisionEngine
from code.output.validator import OutputValidator
import code.config as cfg

class TestEndToEndPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dataset_dir = Path("dataset")
        loader = CSVDataLoader(dataset_dir)
        df_id = loader.load_user_identities()
        df_aud = loader.load_user_audit_log()
        df_man = loader.load_evidence_manifest()
        df_act = loader.load_system_activity()
        df_rules = loader.load_deletion_rules()
        cls.df_samples = loader.load_sample_deletion_requests()

        resolver = IdentityResolver(df_id, df_aud)
        indexer = EvidenceIndexer(dataset_dir, df_man, df_act)
        policy_engine = PolicyEngine(PolicyRulesLoader(df_rules))
        reconstructor = StateReconstructor(df_act, df_man, indexer)
        planner = RemediationPlanner(policy_engine)
        cls.engine = DeletionDecisionEngine(resolver, reconstructor, planner)

    def test_sample_case_01_complete(self):
        req = self.df_samples[self.df_samples["case_id"] == "case_01"].iloc[0]
        cid, status, steps = self.engine.process_request(req)
        self.assertEqual(cid, "case_01")
        self.assertEqual(status, cfg.STATUS_COMPLETE)
        self.assertGreater(len(steps), 0)
        errors = OutputValidator.validate_steps(cid, status, steps)
        self.assertEqual(len(errors), 0)

    def test_sample_case_02_complete(self):
        req = self.df_samples[self.df_samples["case_id"] == "case_02"].iloc[0]
        cid, status, steps = self.engine.process_request(req)
        self.assertEqual(cid, "case_02")
        self.assertEqual(status, cfg.STATUS_COMPLETE)
        self.assertGreater(len(steps), 0)
        errors = OutputValidator.validate_steps(cid, status, steps)
        self.assertEqual(len(errors), 0)

    def test_sample_case_07_incomplete(self):
        req = self.df_samples[self.df_samples["case_id"] == "case_07"].iloc[0]
        cid, status, steps = self.engine.process_request(req)
        self.assertEqual(cid, "case_07")
        self.assertEqual(status, cfg.STATUS_INCOMPLETE)
        self.assertGreater(len(steps), 0)
        errors = OutputValidator.validate_steps(cid, status, steps)
        self.assertEqual(len(errors), 0)

    def test_sample_case_04_complete(self):
        req = self.df_samples[self.df_samples["case_id"] == "case_04"].iloc[0]
        cid, status, steps = self.engine.process_request(req)
        self.assertEqual(cid, "case_04")
        self.assertEqual(status, cfg.STATUS_COMPLETE)
        errors = OutputValidator.validate_steps(cid, status, steps)
        self.assertEqual(len(errors), 0)

if __name__ == "__main__":
    unittest.main()
