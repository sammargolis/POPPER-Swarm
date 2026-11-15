"""Benchmark hypothesis loaders compatible with snap-stanford/POPPER and BixBench3."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


class BixBenchHypothesisBenchmark:
    """Loads BixBench3 study reproduction hypotheses and falsification ledger entries."""

    def __init__(self, task_id: int = 9, path: str = "outputs") -> None:
        self.task_id = task_id
        self.path = Path(path)

    def get_example(self, index: int = 0) -> Dict[str, Any]:
        ledger_path = self.path / "popper_ledger.json"
        if ledger_path.exists():
            data = json.loads(ledger_path.read_text(encoding="utf-8"))
            evals: List[Dict[str, Any]] = data.get("ledgers", [])
            task_evals = [e for e in evals if e.get("task_number") == self.task_id] or evals
            if task_evals:
                item = task_evals[index % len(task_evals)]
                return {
                    "task_id": item.get("task_number"),
                    "artifact_name": item.get("artifact_id"),
                    "prompt": f"Artifact {item.get('artifact_id')} satisfies all biological and structural invariants of Task {item.get('task_number')}.",
                    "round": item.get("stage_label"),
                    "e_value": item.get("cumulative_e_value"),
                    "binary_answer": item.get("decision") == "ACCEPTED",
                }
        return {
            "task_id": self.task_id,
            "artifact_name": "t98g_c10_vs_control_degs.csv",
            "prompt": "REST knockout in T98G clone C10 derepresses canonical neuronal target genes (SNAP25, SYP, SYN1, BDNF) with stripped Ensembl IDs.",
            "binary_answer": True,
        }


def gene_perturb_hypothesis(
    num_of_samples: int = 20,
    permuted: bool = False,
    dataset: str = "IL2",
    path: str = "outputs",
) -> BixBenchHypothesisBenchmark:
    """Return a POPPER-compatible biological hypothesis benchmark loader."""
    task_id = 9 if dataset.upper() in ("IL2", "TAGSEQ", "TASK9") else 11
    return BixBenchHypothesisBenchmark(task_id=task_id, path=path)


def discovery_bench_hypothesis(
    num_samples: int = 20,
    path: str = "outputs",
) -> BixBenchHypothesisBenchmark:
    """Return a POPPER-compatible discovery benchmark loader."""
    return BixBenchHypothesisBenchmark(task_id=11, path=path)
