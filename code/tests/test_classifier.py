"""Unit tests for the RequestClassifier component."""

import unittest
from code.agent.request_classifier import RequestClassifier

class TestRequestClassifier(unittest.TestCase):
    def test_explicit_deletion_english(self):
        self.assertTrue(
            RequestClassifier.is_deletion_request(
                "Please delete my account and erase all my personal data."
            )
        )
        self.assertTrue(
            RequestClassifier.is_deletion_request(
                "I would like to permanently remove all records associated with this address."
            )
        )
        self.assertTrue(
            RequestClassifier.is_deletion_request(
                "Kindly forget my information and purge my profile from your systems."
            )
        )

    def test_multilingual_deletion(self):
        # Spanish
        self.assertTrue(
            RequestClassifier.is_deletion_request(
                "Por favor eliminar mi cuenta y borrar todos mis datos personales."
            )
        )
        # French
        self.assertTrue(
            RequestClassifier.is_deletion_request(
                "Veuillez supprimer mon compte et effacer mes données personnelles."
            )
        )
        # German
        self.assertTrue(
            RequestClassifier.is_deletion_request(
                "Bitte mein Konto löschen und alle Daten entfernen."
            )
        )
        # Portuguese
        self.assertTrue(
            RequestClassifier.is_deletion_request(
                "Solicito a exclusão da minha conta e de todos os meus dados."
            )
        )

    def test_non_deletion_inquiries(self):
        # Data export / portability inquiry
        self.assertFalse(
            RequestClassifier.is_deletion_request(
                "Can you please send me a full export copy of my purchase history and profile?"
            )
        )
        # Privacy policy inquiry
        self.assertFalse(
            RequestClassifier.is_deletion_request(
                "Where can I find your updated terms of service and privacy statement?"
            )
        )
        # General support / billing inquiry
        self.assertFalse(
            RequestClassifier.is_deletion_request(
                "I would like to update my billing address and credit card on file."
            )
        )

if __name__ == "__main__":
    unittest.main()
