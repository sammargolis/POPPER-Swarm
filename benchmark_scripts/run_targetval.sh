#!/usr/bin/env bash
# TargetVal & Gene Perturbation Hypothesis Validation Benchmark (snap-stanford/POPPER compatible)
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-}:$(pwd)/src:$(pwd)"

for seed in 1 2 3 4 5; do
  for dataset in "IFNG" "IL2"; do
    python benchmark_scripts/run_bixbench3_benchmark.py \
      --e_value --relevance_checker --react --seed "$seed" --dataset "$dataset"
  done
done
