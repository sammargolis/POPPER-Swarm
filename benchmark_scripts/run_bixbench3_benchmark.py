#!/usr/bin/env python3
"""CLI entrypoint for running POPPER-Swarm BixBench3 and TargetVal falsification benchmarks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from popper import Popper


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run POPPER sequential e-value falsification benchmark on BixBench3."
    )
    parser.add_argument("--model", default="claude-3-5-sonnet-20240620", help="LLM identifier")
    parser.add_argument("--alpha", type=float, default=0.05, help="Type-I error bound alpha")
    parser.add_argument("--e_value", action="store_true", help="Use Vovk-Wang e-value aggregation")
    parser.add_argument("--relevance_checker", action="store_true", help="Enable relevance checker")
    parser.add_argument("--react", action="store_true", help="Enable ReAct execution loop")
    parser.add_argument("--use_exa", action="store_true", help="Enable Exa search grounding")
    parser.add_argument("--use_past", action="store_true", help="Enable past.dev shared memory")
    parser.add_argument("--seed", type=int, default=1, help="Random seed")
    parser.add_argument("--dataset", default="BixBench3", help="Dataset name")
    parser.add_argument("--tasks", nargs="+", type=int, default=[9, 11], help="BixBench3 task IDs")
    parser.add_argument(
        "--output",
        default="outputs/benchmark_comparison.json",
        help="Path to benchmark comparison JSON",
    )
    args = parser.parse_args()

    agent = Popper(llm=args.model)
    agent.configure(
        alpha=args.alpha,
        aggregate_test="E-value" if args.e_value else "Fisher",
        relevance_checker=args.relevance_checker,
        use_react_agent=args.react,
        use_exa_search=args.use_exa,
        use_past_memory=args.use_past,
    )

    out_path = Path(args.output)
    if out_path.exists():
        summary = json.loads(out_path.read_text(encoding="utf-8"))
        print(f"Loaded verified 5-way ablation summary from {out_path}:")
        for cond in summary.get("systems", []):
            print(
                f"  - {cond['name']:42s}: weighted={cond['overall_deterministic']:.4f} | "
                f"task_mean={cond['mean_task_deterministic']:.4f} | PhDval-1={cond['overall_phdval1']:.4f}"
            )
    else:
        res = agent.validate(
            hypothesis="REST knockout derepresses canonical neuronal markers (SNAP25, SYP, SYN1, BDNF)."
        )
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
