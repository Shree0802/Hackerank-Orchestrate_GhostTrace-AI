"""Unit tests for the IdentityResolver component."""

import unittest
import pandas as pd
from code.identity.resolver import IdentityResolver

class TestIdentityResolver(unittest.TestCase):
    def setUp(self):
        df_identities = pd.DataFrame([
            {
                "user_id": "user_101",
                "name": "Jane Doe",
                "email": "jane.doe@example.com",
                "phone": "+1-555-0101",
                "email_hash": "hash_101",
                "updated_at": "2026-01-01T00:00:00Z",
            }
        ])
        df_audit = pd.DataFrame([
            {
                "audit_id": "aud_01",
                "user_id": "user_101",
                "event_time": "2026-03-01T10:00:00Z",
                "field_name": "email",
                "old_value": "old.jane@example.com",
                "new_value": "jane.doe@example.com",
            },
            {
                "audit_id": "aud_02",
                "user_id": "user_101",
                "event_time": "2026-03-01T10:00:00Z",
                "field_name": "email_hash",
                "old_value": "old_hash_101",
                "new_value": "hash_101",
            }
        ])
        self.resolver = IdentityResolver(df_identities, df_audit)

    def test_resolve_current_email(self):
        user = self.resolver.resolve_email("jane.doe@example.com")
        self.assertIsNotNone(user)
        self.assertEqual(user.user_id, "user_101")
        self.assertIn("old.jane@example.com", user.all_emails)
        self.assertIn("jane.doe@example.com", user.all_emails)
        self.assertIn("old_hash_101", user.all_hashes)

    def test_resolve_historical_email(self):
        user = self.resolver.resolve_email("old.jane@example.com")
        self.assertIsNotNone(user)
        self.assertEqual(user.user_id, "user_101")
        self.assertEqual(user.current_email, "jane.doe@example.com")

    def test_unknown_email(self):
        user = self.resolver.resolve_email("stranger@unknown.com")
        self.assertIsNone(user)

if __name__ == "__main__":
    unittest.main()
