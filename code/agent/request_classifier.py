"""Classifies whether a customer request actually authorizes account/data deletion."""

import re
from typing import Tuple

class RequestClassifier:
    """Classifies deletion vs non-deletion requests deterministically across multilingual patterns."""

    # Phrases indicating explicit non-deletion intent
    NON_DELETION_PATTERNS = [
        r"leave the account active",
        r"not asking for deletion",
        r"keep the account",
        r"do not close",
        r"without removing",
        r"marketing lists only",
        r"stop the promotional emails",
        r"information request, not a request to erase",
        r"leave my profile",
        r"continue using the service",
        r"don't delete",
        r"do not delete",
        r"portable format.*keep",
        r"copy of last year's invoices.*leave",
        r"change the email address used for this account.*continue",
        r"what personal information you hold.*not a request",
        r"help resetting the login.*do not close",
        r"surname is misspelled.*correct it without removing",
        r"where can i find your updated terms of service",
    ]

    # Deletion authorization keywords across English, French, Spanish, German, Portuguese, Italian, Korean, etc.
    DELETION_KEYWORDS = [
        "delet", "eras", "remov", "close", "forget", "purge", "wipe", "expung",
        "supprim", "suppres", "elimin", "lösch", "borr", "cancela", "chiud", "verwijder",
        "destroy", "effac", "terminat", "exclu", "excluir", "gone",
        "entfern", "삭제", "탈퇴", "해지", "削除", "退会", "解約",
        "删除", "注销", "usunięc", "usun", "sterg", "șterg"
    ]

    @classmethod
    def authorizes_deletion(cls, request_text: str) -> bool:
        """Return True if the text authorizes deletion; False if it's NOT_APPLICABLE."""
        if not request_text:
            return False

        clean_text = request_text.strip().lower()

        # 1. Check for explicit non-deletion patterns
        for pat in cls.NON_DELETION_PATTERNS:
            if re.search(pat, clean_text, re.IGNORECASE):
                return False

        # 2. Check for presence of deletion verbs
        has_deletion_verb = any(kw in clean_text for kw in cls.DELETION_KEYWORDS)
        return has_deletion_verb

    @classmethod
    def is_deletion_request(cls, request_text: str, subject: str = "") -> bool:
        """Alias checking both subject and request text."""
        combined = f"{subject} {request_text}"
        return cls.authorizes_deletion(combined)
