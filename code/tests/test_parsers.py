"""Unit tests for evidence parsers (SQL, JSON, Log)."""

import unittest
from pathlib import Path
from code.evidence.sql_inspector import SQLEvidenceInspector
from code.evidence.json_parser import JSONEvidenceParser
from code.evidence.log_parser import LogEvidenceParser

class TestEvidenceParsers(unittest.TestCase):
    def test_sql_replica_parsing(self):
        sql_path = Path("dataset/evidence/databases/customer_data_read_replica_20260921.sql")
        if sql_path.exists():
            obs = SQLEvidenceInspector.parse_file(sql_path, "evidence_05", "2026-09-21T10:00:00Z")
            self.assertGreater(len(obs), 0)
            search_obs = [o for o in obs if o["resource_id"] == "search_1007"]
            self.assertGreater(len(search_obs), 0)
            self.assertEqual(search_obs[0]["system_id"], "search_service")
            self.assertIn("diya.k4436@outlook.com", search_obs[0]["user_identifiers"])

    def test_service_export_parsing(self):
        export_path = Path("dataset/evidence/records/service_resource_export_20260915_114455.json")
        if export_path.exists():
            obs = JSONEvidenceParser.parse_file(export_path, "evidence_92", "2026-09-15T11:44:55Z")
            self.assertGreater(len(obs), 0)
            acc_404 = [o for o in obs if o["resource_id"] == "account_3136"]
            self.assertEqual(len(acc_404), 1)
            self.assertEqual(acc_404[0]["status"], "NOT_FOUND")

    def test_log_trace_correlation(self):
        log_path = Path("dataset/evidence/logs/structured_service_events_eu_west_20260918.log")
        if log_path.exists():
            obs = LogEvidenceParser.parse_file(log_path, "evidence_94", "2026-09-18T12:00:00Z")
            self.assertGreater(len(obs), 0)
            audit_obs = [o for o in obs if o["resource_id"] == "audit_record_4902"]
            self.assertEqual(len(audit_obs), 1)
            self.assertIn("user_61", audit_obs[0]["user_identifiers"])

if __name__ == "__main__":
    unittest.main()
