"""Data loaders and benchmark utilities for POPPER and BixBench3."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd


class ExperimentalDataLoader:
    """Loader for biological perturbation and GTEx/TargetVal tables."""

    def __init__(
        self,
        data_path: str,
        table_dict_selection: str = "all_bio",
        data_sampling: int = -1,
    ) -> None:
        self.data_path = Path(data_path)
        self.table_dict_selection = table_dict_selection
        self.data_sampling = data_sampling
        self.tables: Dict[str, pd.DataFrame] = {}

    def list_tables(self) -> List[str]:
        if not self.data_path.exists():
            return []
        return sorted(p.name for p in self.data_path.glob("*.csv")) + sorted(
            p.name for p in self.data_path.glob("*.tsv")
        )


class BixBench3DataLoader:
    """Loader for BixBench3 raw-FASTQ and downstream study workspaces."""

    def __init__(self, data_path: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.data_path = Path(data_path)
        self.metadata = metadata or {}

    def list_artifacts(self) -> List[Path]:
        if not self.data_path.exists():
            return []
        return sorted(self.data_path.glob("*.csv")) + sorted(self.data_path.glob("*.tsv"))


class CustomDataLoader:
    """Loader for custom CSV/TSV/PKL domain datasets."""

    def __init__(self, data_folder: str) -> None:
        self.data_folder = Path(data_folder)


class DiscoveryBenchDataLoader:
    """Loader for DiscoveryBench multi-domain hypotheses."""

    def __init__(self, data_path: str, metadata: Dict[str, Any]) -> None:
        self.data_path = Path(data_path)
        self.metadata = metadata
