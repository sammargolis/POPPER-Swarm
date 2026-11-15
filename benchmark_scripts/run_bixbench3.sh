#!/usr/bin/env bash
# Reproduce BixBench3 5-way controlled ablation and POPPER sequential falsification benchmark
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-}:$(pwd)/src:$(pwd)"

PYTHON_BIN="python3"
if [ -x ".venv/bin/python3" ]; then
  PYTHON_BIN=".venv/bin/python3"
fi

echo "=== Running POPPER-Swarm BixBench3 5-Way Ablation Benchmark ==="
"$PYTHON_BIN" benchmark_scripts/run_bixbench3_benchmark.py \
  --e_value \
  --relevance_checker \
  --react \
  --use_exa \
  --use_past \
  --alpha 0.05 \
  --tasks 9 11 \
  --output outputs/benchmark_comparison.json
