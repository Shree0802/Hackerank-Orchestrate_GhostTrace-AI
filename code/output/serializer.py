"""Serializes deletion audit decisions into official CSV submission format."""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
import pandas as pd

class OutputSerializer:
    """Safely serializes case audit decisions into output.csv matching the official schema."""

    @staticmethod
    def serialize_to_csv(
        results: List[Tuple[str, str, List[Dict[str, Any]]]],
        output_path: Path,
    ):
        """Write results to CSV file.
        
        results: list of (case_id, deletion_status, steps)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Sort by case_id numerically if possible (e.g. case_1, case_2, ..., case_550)
        def case_sort_key(item):
            cid = item[0]
            if cid.startswith("case_"):
                try:
                    return (0, int(cid.split("_")[1]))
                except ValueError:
                    return (1, cid)
            return (2, cid)

        sorted_results = sorted(results, key=case_sort_key)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["case_id", "deletion_status", "steps_json"])
            for cid, status, steps in sorted_results:
                # Ensure steps is valid json string
                steps_str = json.dumps(steps, separators=(",", ":"))
                writer.writerow([cid, status, steps_str])
