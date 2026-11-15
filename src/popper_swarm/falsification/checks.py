"""Executable POPPER Falsification Checks for Computational Biology Artifacts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from .evalues import (
    ArtifactFalsificationLedger,
    FalsificationTestResult,
    p_to_calibrated_e_value,
)


def run_popper_falsification_battery(
    *,
    artifact_spec: dict[str, Any],
    candidate_path: Path,
    round_index: int = 1,
    alpha: float = 0.05,
    biological_priors: dict[str, Any] | None = None,
) -> ArtifactFalsificationLedger:
    """Run the 6-stage POPPER sequential falsification suite on a candidate artifact file.

    1. Existence & Non-Empty Falsifier (`F1_EXISTENCE`)
    2. Schema & Column Contract Falsifier (`F2_COLUMN_CONTRACT`)
    3. Row-Key Namespace & Version-Suffix Falsifier (`F3_ROWKEY_NAMESPACE`)
    4. NA / Inf / Duplicate Integrity Falsifier (`F4_NUMERIC_INTEGRITY`)
    5. Statistical Distribution & Multiple-Testing Monotonicity Falsifier (`F5_STAT_COHERENCE`)
    6. Biological Contrast Sign & Prior Alignment Falsifier (`F6_BIO_PRIOR_ALIGNMENT`)
    """
    artifact_id = str(artifact_spec.get("artifact_id", candidate_path.stem))
    ledger = ArtifactFalsificationLedger(
        artifact_id=artifact_id,
        round_index=round_index,
        alpha=alpha,
    )

    expected_format = str(artifact_spec.get("output_format", "csv")).lower()
    row_key = str(artifact_spec.get("row_key") or "")
    value_columns = list(artifact_spec.get("value_columns") or [])
    required_columns = list(artifact_spec.get("required_columns") or [])
    if not required_columns and row_key:
        required_columns = [row_key, *value_columns]

    # --- Test 1: Existence & Parseability ---
    if not candidate_path.is_file() or candidate_path.stat().st_size == 0:
        ledger.tests.append(
            FalsificationTestResult(
                test_id="F1_EXISTENCE",
                artifact_id=artifact_id,
                hypothesis_statement=f"Artifact `{artifact_id}` exists and is non-empty at `{candidate_path.name}`.",
                null_implication_tested="File exists on disk with size > 0 bytes and valid tabular header.",
                passed=False,
                e_value=5000.0,
                p_value_equivalent=1e-8,
                observed_statistic="Missing or 0-byte file",
                expected_contract=f"Non-empty {expected_format.upper()} file at {candidate_path}",
                remediation_prescription=f"Ensure pipeline writes `{candidate_path}` before completion.",
            )
        )
        return ledger

    sep = "\t" if expected_format == "tsv" or candidate_path.suffix.lower() == ".tsv" else ","
    try:
        df = pd.read_csv(candidate_path, sep=sep, low_memory=False)
    except Exception as exc:
        ledger.tests.append(
            FalsificationTestResult(
                test_id="F1_EXISTENCE",
                artifact_id=artifact_id,
                hypothesis_statement=f"Artifact `{artifact_id}` is a valid {expected_format.upper()} table.",
                null_implication_tested="Table parses cleanly without parser errors.",
                passed=False,
                e_value=5000.0,
                p_value_equivalent=1e-8,
                observed_statistic=f"ParserError: {exc}",
                expected_contract=f"Valid {expected_format.upper()} delimiter ({sep!r})",
                remediation_prescription=f"Re-export `{candidate_path}` using exact delimiter {sep!r} and UTF-8 encoding.",
            )
        )
        return ledger

    if len(df) == 0:
        ledger.tests.append(
            FalsificationTestResult(
                test_id="F1_EXISTENCE",
                artifact_id=artifact_id,
                hypothesis_statement=f"Artifact `{artifact_id}` contains >= 1 data rows.",
                null_implication_tested="Row count N > 0.",
                passed=False,
                e_value=5000.0,
                p_value_equivalent=1e-8,
                observed_statistic="0 rows",
                expected_contract=">= 1 rows",
                remediation_prescription="Filter thresholds or ID joins produced an empty table; inspect upstream join keys and p-value cutoffs.",
            )
        )
        return ledger

    ledger.tests.append(
        FalsificationTestResult(
            test_id="F1_EXISTENCE",
            artifact_id=artifact_id,
            hypothesis_statement=f"Artifact `{artifact_id}` is parseable and populated.",
            null_implication_tested="Row count N > 0 and valid delimiter.",
            passed=True,
            e_value=0.5,
            p_value_equivalent=1.0,
            observed_statistic=f"{len(df)} rows x {len(df.columns)} cols",
            expected_contract=f"Non-empty {expected_format.upper()}",
            remediation_prescription="None",
        )
    )

    # --- Test 2: Schema, First-Column Row Key, and Required Columns ---
    actual_cols = [str(c) for c in df.columns]
    missing_cols = [c for c in required_columns if c not in actual_cols]
    first_col_ok = (not row_key) or (actual_cols and actual_cols[0] == row_key)
    col_passed = (len(missing_cols) == 0) and first_col_ok

    ledger.tests.append(
        FalsificationTestResult(
            test_id="F2_COLUMN_CONTRACT",
            artifact_id=artifact_id,
            hypothesis_statement=f"Columns of `{artifact_id}` satisfy the output schema with `{row_key}` as column 0.",
            null_implication_tested="All required columns present and row_key is first column.",
            passed=col_passed,
            e_value=0.5 if col_passed else 2500.0,
            p_value_equivalent=1.0 if col_passed else 1e-7,
            observed_statistic=f"first_col={actual_cols[0] if actual_cols else None}, missing={missing_cols}",
            expected_contract=f"row_key={row_key} at col[0]; required={required_columns}",
            remediation_prescription=(
                "None"
                if col_passed
                else f"Rename/reorder columns so `{row_key}` is first and include missing columns: {missing_cols}."
            ),
        )
    )
    if not col_passed or not row_key or row_key not in df.columns:
        return ledger

    # --- Test 3: Row-Key Namespace, Version Suffixes & Uniqueness ---
    key_series = df[row_key].astype(str).str.strip()
    n_dups = int(key_series.duplicated().sum())
    n_na_keys = int(df[row_key].isna().sum() + key_series.isin(["", "NA", "nan", "None"]).sum())
    example_keys = artifact_spec.get("example_keys") or []
    expects_version_suffix = artifact_spec.get("expects_version_suffix")

    suffix_violation = False
    suffix_msg = "OK"
    sample_key = key_series.iloc[0] if len(key_series) > 0 else ""

    if expects_version_suffix is False and re.match(r"^ENS[A-Z]*G\d+\.\d+$", sample_key):
        suffix_violation = True
        suffix_msg = f"Found versioned Ensembl ID `{sample_key}` when unversioned `ENSG...` is required"
    elif expects_version_suffix is True and re.match(r"^ENS[A-Z]*G\d+$", sample_key):
        suffix_violation = True
        suffix_msg = f"Found unversioned Ensembl ID `{sample_key}` when versioned `ENSG... .1` is required"

    namespace_violation = False
    if row_key == "wormbase_gene_id" and not sample_key.startswith("WBGene"):
        namespace_violation = True
        suffix_msg = f"Expected `WBGene...` identifier for `wormbase_gene_id`, got `{sample_key}`"
    elif artifact_spec.get("forbid_wbgene") and sample_key.startswith("WBGene"):
        namespace_violation = True
        suffix_msg = f"Expected public WS235 feature/locus `gene_id` (e.g. `21ur-1`, `AC3.12`), got `WBGene` ID `{sample_key}`"
    elif artifact_spec.get("required_key_prefix") and not sample_key.startswith(str(artifact_spec["required_key_prefix"])):
        namespace_violation = True
        suffix_msg = f"Expected `{row_key}` prefix `{artifact_spec['required_key_prefix']}`, got `{sample_key}`"
    elif row_key == "go_id" and not re.match(r"^GO:\d{7}$", sample_key):
        namespace_violation = True
        suffix_msg = f"Expected `GO:XXXXXXX` identifier for `go_id`, got `{sample_key}`"
    elif row_key == "gene_probe_id" and not re.search(r"_\d+$", sample_key):
        namespace_violation = True
        suffix_msg = (
            f"Expected BioSpyder TempO-Seq `PROBE_NAME` with `_<probe_id>` suffix (e.g. `Cyp2b10_13605`), "
            f"got collapsed symbol `{sample_key}`"
        )
    elif row_key == "contrast_gene_id" and not re.match(r"^day(?:7|28|90)\|\d+ppm\|.+_\d+$", sample_key):
        namespace_violation = True
        suffix_msg = (
            f"Expected composite key `timepoint|concentration|gene_probe_id` (e.g. `day90|6000ppm|Cyp2b10_13605`), "
            f"got `{sample_key}`"
        )
    elif row_key in ("gsea_result_id", "hypergeometric_result_id") and not re.match(
        r"^day(?:7|28|90)\|\d+ppm\|(?:up|down|non_directional)\|.+", sample_key
    ):
        namespace_violation = True
        suffix_msg = (
            f"Expected composite key `timepoint|concentration|direction|gene_set`, got `{sample_key}`"
        )
    elif row_key == "dna_damage_result_id":
        if not re.match(r"^day(?:7|28|90)\|\d+ppm\|.+", sample_key):
            namespace_violation = True
            suffix_msg = f"Expected composite key `timepoint|concentration|gene_set`, got `{sample_key}`"
        elif key_series.str.contains("GO_CELLULAR_RESPONSE_TO_DNA_DAMAGE_STIMULUS", regex=False).any():
            namespace_violation = True
            suffix_msg = "Found excluded gene set `GO_CELLULAR_RESPONSE_TO_DNA_DAMAGE_STIMULUS` in `dna_damage_result_id`"

    expected_row_count = artifact_spec.get("expected_row_count")
    if expected_row_count is not None and len(df) != int(expected_row_count):
        namespace_violation = True
        suffix_msg = f"Expected exactly {expected_row_count} rows per contract grid, got {len(df)}"

    key_passed = (n_dups == 0) and (n_na_keys == 0) and (not suffix_violation) and (not namespace_violation)
    ledger.tests.append(
        FalsificationTestResult(
            test_id="F3_ROWKEY_NAMESPACE",
            artifact_id=artifact_id,
            hypothesis_statement=f"Row key `{row_key}` has unique, non-null identifiers in the required namespace.",
            null_implication_tested="0 duplicate keys, 0 null keys, exact ID namespace/version suffix format.",
            passed=key_passed,
            e_value=0.5 if key_passed else 2500.0,
            p_value_equivalent=1.0 if key_passed else 1e-7,
            observed_statistic=f"dups={n_dups}, na_keys={n_na_keys}, sample_key={sample_key!r} ({suffix_msg})",
            expected_contract=f"Unique non-null `{row_key}` matching contract ({example_keys[:2]})",
            remediation_prescription=(
                "None"
                if key_passed
                else f"Fix `{row_key}`: deduplicate rows (dups={n_dups}), drop NA keys ({n_na_keys}), and fix ID format ({suffix_msg})."
            ),
        )
    )

    # --- Test 4: Numeric Value & Categorical Label Integrity (No All-NA / Inf / Invalid Labels) ---
    check_num_cols = [c for c in value_columns if c in df.columns]
    bad_num_cols: list[str] = []
    for col in check_num_cols:
        num = pd.to_numeric(df[col], errors="coerce")
        na_frac = float(num.isna().mean())
        if na_frac > 0.20:
            bad_num_cols.append(f"{col}(NA={na_frac:.1%})")
        elif np.isinf(num.dropna()).any():
            bad_num_cols.append(f"{col}(has_inf)")

    if "regulation" in df.columns:
        allowed_reg = {"up_vs_control", "down_vs_control"}
        observed_reg = set(df["regulation"].dropna().astype(str).str.strip().unique())
        invalid_reg = sorted(observed_reg - allowed_reg)
        if invalid_reg:
            bad_num_cols.append(f"regulation(invalid_labels={invalid_reg})")

    if "direction" in df.columns:
        allowed_dir = (
            {"up", "down"}
            if artifact_id == "piano_preranked_gsea"
            else {"non_directional", "up", "down"}
        )
        observed_dir = set(df["direction"].dropna().astype(str).str.strip().unique())
        invalid_dir = sorted(observed_dir - allowed_dir)
        if invalid_dir:
            bad_num_cols.append(f"direction(invalid_labels={invalid_dir})")

    num_passed = len(bad_num_cols) == 0
    ledger.tests.append(
        FalsificationTestResult(
            test_id="F4_NUMERIC_INTEGRITY",
            artifact_id=artifact_id,
            hypothesis_statement="Numeric value and categorical label columns contain finite, contract-compliant values.",
            null_implication_tested="NA rate <= 20%, 0 Inf values, and valid categorical labels across all graded columns.",
            passed=num_passed,
            e_value=0.5 if num_passed else 1000.0,
            p_value_equivalent=1.0 if num_passed else 1e-6,
            observed_statistic="All numeric/label columns clean" if num_passed else f"Corrupted columns: {bad_num_cols}",
            expected_contract="Finite numeric values and exact categorical labels in all graded columns",
            remediation_prescription=(
                "None"
                if num_passed
                else f"Remove/impute NA or Inf values or fix label vocabulary in {bad_num_cols}; check join keys or DESeq2 NA filtering."
            ),
        )
    )

    # --- Test 5: Statistical Coherence (Wald Stat Sign vs LFC Sign, BH padj >= pvalue) ---
    stat_issues: list[str] = []
    lfc_col = next((c for c in ("log2_fold_change", "log2FoldChange") if c in df.columns), None)
    stat_col = next((c for c in ("stat", "stat_dist_dir") if c in df.columns), None)
    pval_col = next((c for c in ("p_value", "pvalue") if c in df.columns), None)
    padj_col = next((c for c in ("padj", "fdr") if c in df.columns), None)

    if lfc_col and stat_col:
        lfc_vals = pd.to_numeric(df[lfc_col], errors="coerce")
        stat_vals = pd.to_numeric(df[stat_col], errors="coerce")
        valid = lfc_vals.notna() & stat_vals.notna() & (lfc_vals != 0) & (stat_vals != 0)
        if valid.any():
            sign_mismatch = int((np.sign(lfc_vals[valid]) != np.sign(stat_vals[valid])).sum())
            if sign_mismatch > 0:
                stat_issues.append(f"{sign_mismatch} rows have opposite sign between {lfc_col} and {stat_col}")

    if "direction" in df.columns and "stat_dist_dir" in df.columns:
        dirs = df["direction"].astype(str).str.strip()
        svals = pd.to_numeric(df["stat_dist_dir"], errors="coerce")
        bad_up = int(((dirs == "up") & (svals < 0)).sum())
        bad_down = int(((dirs == "down") & (svals > 0)).sum())
        if bad_up + bad_down > 0:
            stat_issues.append(
                f"{bad_up + bad_down} rows violate directional PIANO statistic sign (up={bad_up}, down={bad_down})"
            )

    if pval_col and padj_col:
        pvals = pd.to_numeric(df[pval_col], errors="coerce")
        padjs = pd.to_numeric(df[padj_col], errors="coerce")
        valid = pvals.notna() & padjs.notna()
        if valid.any():
            inversions = int((padjs[valid] + 1e-12 < pvals[valid]).sum())
            if inversions > 0:
                stat_issues.append(f"{inversions} rows have {padj_col} < {pval_col}")

    for suffix in ("non_directional", "up", "down"):
        pv_c = f"p_value_{suffix}"
        fdr_c = f"fdr_{suffix}"
        if pv_c in df.columns and fdr_c in df.columns:
            pvals = pd.to_numeric(df[pv_c], errors="coerce")
            padjs = pd.to_numeric(df[fdr_c], errors="coerce")
            valid = pvals.notna() & padjs.notna()
            if valid.any():
                inversions = int((padjs[valid] + 1e-12 < pvals[valid]).sum())
                if inversions > 0:
                    stat_issues.append(f"{inversions} rows have {fdr_c} < {pv_c}")

    max_padj = artifact_spec.get("max_padj")
    if max_padj is not None and padj_col and padj_col in df.columns:
        padjs = pd.to_numeric(df[padj_col], errors="coerce")
        over_thresh = int((padjs > float(max_padj) + 1e-9).sum())
        if over_thresh > 0:
            stat_issues.append(f"{over_thresh} rows exceed significance cutoff {padj_col} <= {max_padj}")

    min_abs_lfc = artifact_spec.get("min_abs_lfc")
    if min_abs_lfc is not None and lfc_col and lfc_col in df.columns:
        lfcs = pd.to_numeric(df[lfc_col], errors="coerce")
        under_lfc = int((lfcs.abs() + 1e-6 < float(min_abs_lfc)).sum())
        if under_lfc > 0:
            stat_issues.append(f"{under_lfc} rows fail |{lfc_col}| >= {min_abs_lfc:.4f}")

    min_lfc = artifact_spec.get("min_lfc")
    if min_lfc is not None and lfc_col and lfc_col in df.columns:
        lfcs = pd.to_numeric(df[lfc_col], errors="coerce")
        bad_min = int((lfcs + 1e-6 < float(min_lfc)).sum())
        if bad_min > 0:
            stat_issues.append(f"{bad_min} rows fail {lfc_col} >= {min_lfc:.4f}")

    max_lfc = artifact_spec.get("max_lfc")
    if max_lfc is not None and lfc_col and lfc_col in df.columns:
        lfcs = pd.to_numeric(df[lfc_col], errors="coerce")
        bad_max = int((lfcs - 1e-6 > float(max_lfc)).sum())
        if bad_max > 0:
            stat_issues.append(f"{bad_max} rows fail {lfc_col} <= {max_lfc:.4f}")

    excluded_genes = set(artifact_spec.get("excluded_genes") or [])
    if excluded_genes:
        for gcol in ("gene_id", "gene_symbol", row_key):
            if gcol in df.columns:
                overlap = sorted(set(df[gcol].astype(str).str.strip()) & excluded_genes)
                if overlap:
                    stat_issues.append(
                        f"{len(overlap)} rows overlap with excluded shared-signature genes ({overlap[:4]})"
                    )
                    break

    stat_passed = len(stat_issues) == 0
    ledger.tests.append(
        FalsificationTestResult(
            test_id="F5_STAT_COHERENCE",
            artifact_id=artifact_id,
            hypothesis_statement="Statistical test columns obey sign coherence, BH monotonicity (padj >= pvalue), and prompt filter thresholds.",
            null_implication_tested="sign(LFC) == sign(stat), padj >= pvalue, and all rows satisfy stated significance thresholds.",
            passed=stat_passed,
            e_value=0.5 if stat_passed else 1500.0,
            p_value_equivalent=1.0 if stat_passed else 1e-6,
            observed_statistic="Coherent" if stat_passed else "; ".join(stat_issues),
            expected_contract="Consistent Wald/LFC signs, padj >= pvalue, and exact significance filtering",
            remediation_prescription=(
                "None"
                if stat_passed
                else f"Fix statistical violations: {'; '.join(stat_issues)}."
            ),
        )
    )

    # --- Test 6: Biological Contrast Direction & Exa Prior Falsifier ---
    if biological_priors:
        expected_up_genes: list[str] = biological_priors.get("expected_up_genes", [])
        gene_sym_col = next(
            (c for c in ("gene_symbol", "gene_name", "gene_probe_id", row_key) if c in df.columns),
            row_key,
        )
        raw_syms = df[gene_sym_col].astype(str).str.strip()
        stripped_syms = raw_syms.str.replace(r"_\d+$", "", regex=True)
        match_mask = raw_syms.isin(expected_up_genes) | stripped_syms.isin(expected_up_genes)
        sub = df[match_mask]

        if lfc_col and lfc_col in df.columns and len(sub) >= 2:
            lfcs = pd.to_numeric(sub[lfc_col], errors="coerce").dropna()
            frac_positive = float((lfcs > 0).mean()) if len(lfcs) else 1.0
            # Binomial test against inverted contrast (frac_positive < 0.5)
            p_val = float(stats.binomtest(int((lfcs > 0).sum()), len(lfcs), p=0.8, alternative="less").pvalue)
            e_val = p_to_calibrated_e_value(p_val) if frac_positive < 0.5 else 0.5
            bio_passed = frac_positive >= 0.5
            ledger.tests.append(
                FalsificationTestResult(
                    test_id="F6_BIO_PRIOR_ALIGNMENT",
                    artifact_id=artifact_id,
                    hypothesis_statement="Fold-change direction aligns with independent canonical biological marker priors retrieved via Exa.",
                    null_implication_tested=f"Known derepressed/upregulated markers ({expected_up_genes[:4]}) have positive {lfc_col}.",
                    passed=bio_passed,
                    e_value=e_val,
                    p_value_equivalent=round(p_val, 6),
                    observed_statistic=f"{frac_positive:.0%} of canonical markers have positive {lfc_col} (n={len(lfcs)})",
                    expected_contract=">= 50% positive LFC on canonical upregulated targets (verifying treatment/control numerator)",
                    remediation_prescription=(
                        "None"
                        if bio_passed
                        else "Contrast sign is inverted! Relevel DESeq2 control factor (`relevel(condition, ref='control')`) or flip contrast vector."
                    ),
                )
            )
        elif "regulation" in df.columns and len(sub) >= 2:
            regs = sub["regulation"].astype(str).str.strip()
            n_up = int((regs == "up_vs_control").sum())
            frac_positive = float(n_up / len(regs)) if len(regs) else 1.0
            p_val = float(stats.binomtest(n_up, len(regs), p=0.8, alternative="less").pvalue)
            e_val = p_to_calibrated_e_value(p_val) if frac_positive < 0.5 else 0.5
            bio_passed = frac_positive >= 0.5
            ledger.tests.append(
                FalsificationTestResult(
                    test_id="F6_BIO_PRIOR_ALIGNMENT",
                    artifact_id=artifact_id,
                    hypothesis_statement="Shared DEG regulation direction aligns with canonical biological marker priors retrieved via Exa.",
                    null_implication_tested=f"Known derepressed/upregulated markers ({expected_up_genes[:4]}) have regulation == 'up_vs_control'.",
                    passed=bio_passed,
                    e_value=e_val,
                    p_value_equivalent=round(p_val, 6),
                    observed_statistic=f"{frac_positive:.0%} of canonical markers have up_vs_control (n={len(regs)})",
                    expected_contract=">= 50% up_vs_control on canonical upregulated targets",
                    remediation_prescription=(
                        "None"
                        if bio_passed
                        else "Shared DEG regulation labels are inverted relative to canonical biological priors!"
                    ),
                )
            )

    return ledger
