"""Loads and parses dynamic deletion rules from deletion_rules.csv."""

from dataclasses import dataclass
from typing import Dict, List, Optional
import pandas as pd

@dataclass
class DeletionRule:
    rule_id: str
    data_category: str
    condition: str
    required_action: str

class PolicyRulesLoader:
    """Loads deletion rules into structured policy mappings."""

    def __init__(self, df_rules: pd.DataFrame):
        self.rules_by_category: Dict[str, DeletionRule] = {}
        for _, row in df_rules.iterrows():
            cat = str(row["data_category"]).strip()
            rule = DeletionRule(
                rule_id=str(row["rule_id"]).strip(),
                data_category=cat,
                condition=str(row["condition"]).strip(),
                required_action=str(row["required_action"]).strip().upper()
            )
            self.rules_by_category[cat] = rule

    def get_rule(self, category: str) -> Optional[DeletionRule]:
        return self.rules_by_category.get(category.strip())
