"""Structured identity representation and identity graph data structure."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

@dataclass
class UserIdentity:
    """Represents a resolved user identity with current and historical identifiers."""
    user_id: str
    current_name: Optional[str] = None
    current_email: Optional[str] = None
    current_phone: Optional[str] = None
    current_hash: Optional[str] = None
    updated_at: Optional[str] = None
    
    # Complete set of resolved identifiers across all audit history
    all_emails: Set[str] = field(default_factory=set)
    all_phones: Set[str] = field(default_factory=set)
    all_names: Set[str] = field(default_factory=set)
    all_hashes: Set[str] = field(default_factory=set)
    
    # Audit log provenance
    supporting_audit_ids: List[str] = field(default_factory=list)

    def matches_identifier(self, identifier: str) -> bool:
        """Check if an identifier string matches any current or historical identifier."""
        if not identifier:
            return False
        clean = identifier.strip().lower()
        if clean in self.all_emails:
            return True
        if identifier.strip() in self.all_phones:
            return True
        if identifier.strip() in self.all_names:
            return True
        if identifier.strip() in self.all_hashes:
            return True
        if identifier.strip() == self.user_id:
            return True
        return False

    def all_identifiers(self) -> Set[str]:
        """Return the complete set of all known identifiers for this user."""
        res = set()
        res.add(self.user_id)
        res.update(self.all_emails)
        res.update(self.all_phones)
        res.update(self.all_names)
        res.update(self.all_hashes)
        return res
