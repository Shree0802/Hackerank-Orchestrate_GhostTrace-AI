"""Comprehensive evaluation framework computing case status, step precision/recall/F1, and field accuracy."""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
import pandas as pd

class EvaluationMetrics:
    def __init__(self):
        self.total_cases = 0
        self.status_correct = 0
        self.exact_match_cases = 0

        # Step-level metrics
        self.total_pred_steps = 0
        self.total_gold_steps = 0
        self.matched_steps = 0

        # Field-level counts on matched steps
        self.phase_matches = 0
        self.system_matches = 0
        self.resource_matches = 0
        self.operation_matches = 0
        self.state_matches = 0
        self.evidence_matches = 0

        self.case_details = []

    @property
    def status_accuracy(self) -> float:
        return self.status_correct / self.total_cases if self.total_cases > 0 else 0.0

    @property
    def sequence_accuracy(self) -> float:
        return self.exact_match_cases / self.total_cases if self.total_cases > 0 else 0.0

    @property
    def step_precision(self) -> float:
        return self.matched_steps / self.total_pred_steps if self.total_pred_steps > 0 else 0.0

    @property
    def step_recall(self) -> float:
        return self.matched_steps / self.total_gold_steps if self.total_gold_steps > 0 else 0.0

    @property
    def step_f1(self) -> float:
        p = self.step_precision
        r = self.step_recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    def summary_dict(self) -> Dict[str, Any]:
        return {
            "total_cases": self.total_cases,
            "status_accuracy": round(self.status_accuracy, 4),
            "sequence_accuracy": round(self.sequence_accuracy, 4),
            "step_precision": round(self.step_precision, 4),
            "step_recall": round(self.step_recall, 4),
            "step_f1": round(self.step_f1, 4),
            "total_pred_steps": self.total_pred_steps,
            "total_gold_steps": self.total_gold_steps,
            "matched_steps": self.matched_steps,
        }

class Evaluator:
    """Evaluates predicted output CSV against a reference/ground-truth output CSV."""

    @staticmethod
    def evaluate_files(pred_path: Path, gold_path: Path) -> EvaluationMetrics:
        df_pred = pd.read_csv(pred_path)
        df_gold = pd.read_csv(gold_path)

        metrics = EvaluationMetrics()

        pred_map = {r["case_id"]: r for _, r in df_pred.iterrows()}
        gold_map = {r["case_id"]: r for _, r in df_gold.iterrows()}

        for cid, gold_row in gold_map.items():
            metrics.total_cases += 1
            if cid not in pred_map:
                metrics.case_details.append({
                    "case_id": cid,
                    "error": "Missing from predictions",
                    "status_match": False,
                    "exact_match": False,
                })
                continue

            pred_row = pred_map[cid]

            gold_status = gold_row["deletion_status"]
            pred_status = pred_row["deletion_status"]

            status_match = (gold_status == pred_status)
            if status_match:
                metrics.status_correct += 1

            gold_steps = json.loads(gold_row["steps_json"])
            pred_steps = json.loads(pred_row["steps_json"])

            metrics.total_gold_steps += len(gold_steps)
            metrics.total_pred_steps += len(pred_steps)

            # Compare steps
            exact_match = (status_match and gold_steps == pred_steps)
            if exact_match:
                metrics.exact_match_cases += 1

            # Match steps by (phase, resource_id, operation)
            gold_keys = {
                (s["phase"], s["resource_id"], s["operation"]): s for s in gold_steps
            }
            pred_keys = {
                (s["phase"], s["resource_id"], s["operation"]): s for s in pred_steps
            }

            for k, g_step in gold_keys.items():
                if k in pred_keys:
                    metrics.matched_steps += 1
                    p_step = pred_keys[k]
                    if p_step.get("phase") == g_step.get("phase"):
                        metrics.phase_matches += 1
                    if p_step.get("system_id") == g_step.get("system_id"):
                        metrics.system_matches += 1
                    if p_step.get("resource_id") == g_step.get("resource_id"):
                        metrics.resource_matches += 1
                    if p_step.get("operation") == g_step.get("operation"):
                        metrics.operation_matches += 1
                    if p_step.get("state") == g_step.get("state"):
                        metrics.state_matches += 1
                    if p_step.get("evidence_id") == g_step.get("evidence_id"):
                        metrics.evidence_matches += 1

            metrics.case_details.append({
                "case_id": cid,
                "gold_status": gold_status,
                "pred_status": pred_status,
                "status_match": status_match,
                "exact_match": exact_match,
                "gold_steps_count": len(gold_steps),
                "pred_steps_count": len(pred_steps),
            })

        return metrics
