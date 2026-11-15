"""Tests for past.dev multi-agent memory, Exa search compliance, and POPPER sequential falsification."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest

from popper_swarm.config import SwarmConfig
from popper_swarm.falsification import (
    p_to_calibrated_e_value,
    run_popper_falsification_battery,
)
from popper_swarm.memory import PastMemoryClient
from popper_swarm.search import (
    EXA_LLM_SYSTEM_PROMPT_GUIDANCE,
    EXA_OBJECTIVE_DESCRIPTION,
    ExaResearchClient,
)


def test_exa_canonical_tool_schema_and_sanitizer(tmp_path: Path) -> None:
    """Verify build-with-exa canonical tool schema, objective description, and DOI sanitizer."""
    log_path = tmp_path / "exa_provenance.jsonl"
    client = ExaResearchClient(
        api_key="test-key",
        provenance_log_path=log_path,
        blocked_identifiers=["10.1186/s12915-024-01879-0", "10_1186_s12915_024_01879_0_v1"],
        enabled=False,
    )
    tools = client.tool_definitions_anthropic()
    search_tool = next(t for t in tools if t["name"] == "exa_search")
    assert search_tool["input_schema"]["required"] == ["query", "objective"]
    assert (
        search_tool["input_schema"]["properties"]["objective"]["description"]
        == EXA_OBJECTIVE_DESCRIPTION
    )
    assert "exa_search" in EXA_LLM_SYSTEM_PROMPT_GUIDANCE

    clean_q, removed = client._sanitize_query(
        "DESeq2 10.1186/s12915-024-01879-0 REST knockout 10_1186_s12915_024_01879_0_v1"
    )
    assert "10.1186" not in clean_q
    assert "10_1186" not in clean_q
    assert len(removed) >= 2


def test_popper_falsification_catches_version_suffix_and_inverted_sign(tmp_path: Path) -> None:
    """Verify POPPER Critic catches Ensembl version suffix violations and inverted contrast signs."""
    bad_csv = tmp_path / "bad_degs.csv"
    pd.DataFrame(
        {
            "gene_id": ["ENSG00000100001.1", "ENSG00000100002.2", "ENSG00000100003.1"],
            "gene_symbol": ["SNAP25", "SYP", "SYN1"],
            "base_mean": [120.5, 85.2, 310.0],
            "log2_fold_change": [-2.5, -1.8, -3.1],  # Inverted! Canonical REST targets should be UP (+)
            "lfc_se": [0.3, 0.2, 0.4],
            "stat": [8.3, 9.0, 7.7],  # Sign mismatch with log2_fold_change!
            "p_value": [0.001, 0.0005, 0.0001],
            "padj": [0.0001, 0.01, 0.02],  # padj < p_value on row 0!
        }
    ).to_csv(bad_csv, index=False)

    spec = {
        "artifact_id": "t98g_c10_vs_control_degs",
        "output_format": "csv",
        "row_key": "gene_id",
        "required_columns": [
            "gene_id",
            "gene_symbol",
            "base_mean",
            "log2_fold_change",
            "lfc_se",
            "stat",
            "p_value",
            "padj",
        ],
        "value_columns": ["base_mean", "log2_fold_change", "lfc_se", "stat", "p_value", "padj"],
        "expects_version_suffix": False,
        "max_padj": 0.05,
        "min_abs_lfc": 0.58496,
    }
    ledger_bad = run_popper_falsification_battery(
        artifact_spec=spec,
        candidate_path=bad_csv,
        round_index=1,
        biological_priors={"expected_up_genes": ["SNAP25", "SYP", "SYN1"]},
    )
    assert ledger_bad.rejected is True
    failed_ids = {t.test_id for t in ledger_bad.failed_tests}
    assert "F3_ROWKEY_NAMESPACE" in failed_ids
    assert "F5_STAT_COHERENCE" in failed_ids
    assert "F6_BIO_PRIOR_ALIGNMENT" in failed_ids
    assert ledger_bad.cumulative_e_value >= 20.0

    # Now repair the table according to the Critic's remediation prescription
    good_csv = tmp_path / "good_degs.csv"
    pd.DataFrame(
        {
            "gene_id": ["ENSG00000100001", "ENSG00000100002", "ENSG00000100003"],
            "gene_symbol": ["SNAP25", "SYP", "SYN1"],
            "base_mean": [120.5, 85.2, 310.0],
            "log2_fold_change": [2.5, 1.8, 3.1],
            "lfc_se": [0.3, 0.2, 0.4],
            "stat": [8.3, 9.0, 7.7],
            "p_value": [0.0001, 0.0005, 0.001],
            "padj": [0.001, 0.005, 0.01],
        }
    ).to_csv(good_csv, index=False)

    ledger_good = run_popper_falsification_battery(
        artifact_spec=spec,
        candidate_path=good_csv,
        round_index=2,
        biological_priors={"expected_up_genes": ["SNAP25", "SYP", "SYN1"]},
    )
    assert ledger_good.rejected is False
    assert len(ledger_good.failed_tests) == 0


@pytest.mark.skipif(not os.environ.get("PAST_API_KEY"), reason="requires a live past.dev PAST_API_KEY")
def test_past_memory_multi_agent_cross_reads(tmp_path: Path) -> None:
    """Verify multiple agents write to and read from past.dev with cross-agent attribution."""
    cfg = SwarmConfig()
    trace_file = tmp_path / "past_memory_trace.jsonl"
    client = PastMemoryClient(
        api_key=cfg.past_api_key,
        trace_log_path=trace_file,
        enabled=True,
    )

    # Agent 1 (proposer) writes
    r1 = client.ingest(
        author="proposer",
        task_id="test_task_9",
        category="plan",
        label="Task 9 Plan",
        content="Strip GENCODE .version suffixes on DESeq2 DEG tables but retain them on tagseq_featurecounts_matrix.",
    )
    assert r1.get("http_status") in (200, 202)

    # Agent 2 (inspector) writes
    r2 = client.ingest(
        author="inspector",
        task_id="test_task_9",
        category="data_facts",
        label="Task 9 Sample Sheet Facts",
        content="28 technical Tag-Seq FASTQs map to 16 biological replicates across T98G and HEK293.",
    )
    assert r2.get("http_status") in (200, 202)

    # Agent 3 (experimenter) reads memories written by proposer and inspector
    recalled = client.recall(
        reader="experimenter",
        query="How should GENCODE version suffixes and technical Tag-Seq FASTQ runs be handled?",
        task_id="test_task_9",
    )
    assert len(recalled) >= 2
    cross_authors = {item["author"] for item in recalled if item.get("cross_agent_read")}
    assert "proposer" in cross_authors
    assert "inspector" in cross_authors

    # Agent 4 (critic) reads and writes
    _ = client.recall(
        reader="critic",
        query="What is the GENCODE version suffix rule for Task 9?",
        task_id="test_task_9",
    )
    assert trace_file.exists()
    assert p_to_calibrated_e_value(0.0001) > 20.0
