# Contributing to POPPER-Swarm

Thank you for your interest in contributing to **POPPER-Swarm**!

## Development Workflow

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```
2. Run the test suite before submitting changes:
   ```bash
   pytest -q
   ```
3. Verify the benchmark CLI and live observatory:
   ```bash
   bash benchmark_scripts/run_bixbench3.sh
   uvicorn popper_swarm.dashboard:app --host 127.0.0.1 --port 8765
   ```

## Scientific Rigor Guidelines

- **Never fabricate or placeholder biological identifiers:** Always map Ensembl IDs (`ENSG...`), gene symbols, and TempO-Seq probe IDs directly from the registered study files.
- **Anti-leakage search discipline:** Any Exa search query executed inside a falsification check (`F6_BIO_PRIOR_ALIGNMENT`) must exclude the target study's DOI and accession identifiers.
- **Type-I error control:** Any new falsification check added to `src/popper_swarm/falsification/checks.py` must return a calibrated $p$-value converted via Vovk-Wang calibration ($e_k = \frac{1}{2} p_k^{-1/2}$) and respect Ville's inequality ($E_t = \prod_{k=1}^t e_k \ge 1/\alpha$).
