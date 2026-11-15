#!/usr/bin/env python3
"""Generate publication-quality architecture and benchmark figures for README.md."""

from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "figs"
FIGS.mkdir(parents=True, exist_ok=True)


def build_swarm_illustration() -> None:
    """Create figs/popper_swarm_illustration.png in the visual style of snap-stanford/POPPER."""
    fig, ax = plt.subplots(figsize=(14, 6.2), dpi=220)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6.2)
    ax.axis("off")
    fig.patch.set_facecolor("#ffffff")

    def box(x, y, w, h, title, lines, edge_color, fill_color, title_color, title_fs=10.2, line_fs=8.4):
        rect = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.06,rounding_size=0.14",
            linewidth=2.0,
            edgecolor=edge_color,
            facecolor=fill_color,
        )
        ax.add_patch(rect)
        ax.text(
            x + w / 2, y + h - 0.34, title,
            ha="center", va="center",
            fontsize=title_fs, fontweight="bold", color=title_color, family="sans-serif"
        )
        for idx, line in enumerate(lines):
            ax.text(
                x + w / 2, y + h - 0.78 - idx * 0.36, line,
                ha="center", va="center",
                fontsize=line_fs, color="#1f2937", family="sans-serif"
            )

    # Top Title Banner
    ax.text(
        7.0, 5.92,
        "POPPER-Swarm: Automated Study Validation & Reproduction with Agentic Sequential Falsifications",
        ha="center", va="center", fontsize=13.0, fontweight="bold", color="#111827"
    )

    # 1. Input Study & Type-I Error Rate alpha
    box(
        0.25, 3.05, 2.30, 2.15,
        "1. Inspector Agent",
        [
            "Raw FASTQ Reads (27.3 GB)",
            "Main Hypothesis H",
            "Type-I Error Rate α = 0.05",
            "Writes data_facts -> past.dev",
        ],
        "#64748b", "#f8fafc", "#1e293b"
    )

    # 2. Experiment Design Agent (Proposer + Exa)
    box(
        2.95, 3.05, 2.65, 2.15,
        "2. Experiment Design",
        [
            "Proposer + Exa Web Search",
            "Null Sub-Hypothesis h_0^i",
            "Alt Sub-Hypothesis h_1^i",
            "Pulls GitHub code (/search)",
        ],
        "#15803d", "#f0fdf4", "#166534"
    )

    # 3. Experiment Execution Agent (Experimenter)
    box(
        6.00, 3.05, 2.55, 2.15,
        "3. Execution Agent",
        [
            "Think -> Execute -> Observe",
            "HISAT2 / featureCounts / R",
            "Recalls sample map (past.dev)",
            "Emits Candidate Table A_t",
        ],
        "#1d4ed8", "#eff6ff", "#1e40af"
    )

    # 4. Sequential Error Control (POPPER Critic)
    box(
        8.95, 3.05, 2.70, 2.15,
        "4. Sequential Error Control",
        [
            "POPPER Critic (F1 .. F6)",
            "P-values {p_1, ..., p_k}",
            "E-value: e_k = 0.5 * p_k^(-0.5)",
            "Ville Bound: E_t = ∏ e_k >= 1/α",
        ],
        "#b91c1c", "#fef2f2", "#991b1b"
    )

    # 5. Accepted / Auditor Memory Distillation
    box(
        12.05, 3.05, 1.70, 2.15,
        "5. Auditor",
        [
            "If E_t < 20.0:",
            "Accept Table",
            "Distill rules",
            "to past.dev",
        ],
        "#0f766e", "#f0fdfa", "#0f766e"
    )

    # Forward Arrows
    arrow_kw = dict(arrowstyle="->,head_width=0.25,head_length=0.25", lw=2.0, color="#334155")
    ax.annotate("", xy=(2.92, 4.12), xytext=(2.58, 4.12), arrowprops=arrow_kw)
    ax.annotate("", xy=(5.97, 4.12), xytext=(5.63, 4.12), arrowprops=arrow_kw)
    ax.annotate("", xy=(8.92, 4.12), xytext=(8.58, 4.12), arrowprops=arrow_kw)
    ax.annotate("", xy=(12.02, 4.12), xytext=(11.68, 4.12), arrowprops=arrow_kw)

    # Feedback Loop Arrow (E_t >= 1/alpha = 20.0 -> Reject & Repair)
    ax.plot([10.30, 10.30, 4.27, 4.27], [5.22, 5.54, 5.54, 5.22], ls="--", lw=1.8, color="#991b1b")
    ax.annotate("", xy=(4.27, 5.22), xytext=(4.27, 5.35),
                arrowprops=dict(arrowstyle="->,head_width=0.25,head_length=0.25", lw=1.8, color="#991b1b"))
    ax.text(
        7.28, 5.65,
        "Falsified (E_t >= 1/α = 20.0): Reject hypothesis, log to past.dev, and run repair iteration i + 1",
        ha="center", va="center", fontsize=9.2, fontweight="bold", color="#991b1b"
    )

    # Bottom Callout Left: Exa Literature & Protocol Grounding
    box(
        0.25, 0.35, 6.50, 2.25,
        "Exa Web Search Grounding (+57.0 pts Ablation Gain)",
        [
            "• Method Discovery: Pulls GitHub code (z0on/tag-based_RNAseq) -> 5'-clipper + -s 1",
            "• Biology Direction Check (F6): Queries SNAP25, SYP, Cyp2b10 (target DOI blocked)",
            "• Catches inverted DESeq2 control levels (Round 1 0.0000 -> Round 2 0.8754)",
        ],
        "#1e3a8a", "#f8fafc", "#1e3a8a", title_fs=10.2, line_fs=8.5
    )

    # Bottom Callout Right: past.dev Cross-Agent Shared Memory
    box(
        7.25, 0.35, 6.50, 2.25,
        "past.dev Multi-Agent Memory (+26.3 pts Ablation Gain)",
        [
            "• data_facts (Inspector -> Experimenter): 28-to-16 SRR merge map & 88-set GO filter",
            "• rejected_hypotheses (Critic -> Experimenter): 13 falsified Round-1 tables & fixes",
            "• global_learnings (Auditor -> Proposer): Ensembl .version stripping rule across studies",
        ],
        "#0f766e", "#f8fafc", "#0f766e", title_fs=10.2, line_fs=8.5
    )

    plt.tight_layout()
    fig.savefig(FIGS / "popper_swarm_illustration.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_ablation_chart() -> None:
    """Create figs/bixbench3_ablation_results.png with 2 clean side-by-side panels."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 4.8), dpi=220)
    fig.patch.set_facecolor("#ffffff")

    # Panel A: 5-Way Controlled Ablation
    labels_a = [
        "Single-Agent\nBaseline",
        "Swarm\n(-Exa Search)",
        "Swarm\n(-POPPER Critic)",
        "Swarm\n(-past.dev)",
        "POPPER-Swarm\n(Full)",
    ]
    bix_scores = [0.1615, 0.1710, 0.4662, 0.4783, 0.7413]
    phd_scores = [0.4250, 0.7450, 0.6350, 0.6400, 0.8450]

    x = np.arange(len(labels_a))
    w = 0.35
    colors_bix = ["#94a3b8", "#94a3b8", "#94a3b8", "#94a3b8", "#991b1b"]
    bars1 = ax1.bar(x - w / 2, bix_scores, w, label="Official BixBench3 Grade (19 Tables)", color=colors_bix)
    bars2 = ax1.bar(x + w / 2, phd_scores, w, label="GPT-5.5 PhDval-1 Judge", color="#1e3a8a")

    ax1.axhline(0.5230, color="#991b1b", linestyle="--", linewidth=1.4, label="Public 20-Study Record (0.5230)")
    ax1.set_ylim(0, 1.02)
    ax1.set_ylabel("Score (0.00 to 1.00)", fontsize=10, fontweight="bold")
    ax1.set_title("A. 5-Way Controlled Ablation on BixBench3", fontsize=11.5, fontweight="bold", pad=10)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels_a, fontsize=8.8)
    ax1.grid(axis="y", linestyle=":", alpha=0.6)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.legend(loc="upper left", fontsize=8.2, frameon=True)

    for b in bars1:
        h = b.get_height()
        ax1.text(b.get_x() + b.get_width() / 2, h + 0.018, f"{h:.2f}", ha="center", va="bottom", fontsize=8.2, fontweight="bold")
    for b in bars2:
        h = b.get_height()
        ax1.text(b.get_x() + b.get_width() / 2, h + 0.018, f"{h:.2f}", ha="center", va="bottom", fontsize=8.2, fontweight="bold", color="#1e3a8a")

    # Panel B: Round 1 (Before Critic) vs Round 2 (After POPPER Critic)
    labels_b = [
        "Raw Counts\n(Task 9)",
        "C10 DEGs\n(Task 9)",
        "G2 DEGs\n(Task 9)",
        "HEK293 DEGs\n(Task 9)",
        "Dose DEGs\n(Task 11)",
        "DNA Damage\n(Task 11)",
    ]
    r1_scores = [0.4623, 0.0000, 0.0000, 0.0000, 0.1420, 0.2498]
    r2_scores = [0.9902, 0.9707, 0.9578, 0.8754, 0.9190, 0.5625]

    xb = np.arange(len(labels_b))
    bars_r1 = ax2.bar(xb - w / 2, r1_scores, w, label="Round 1: Before Critic (Falsified E_t >= 20)", color="#94a3b8")
    bars_r2 = ax2.bar(xb + w / 2, r2_scores, w, label="Round 2: After POPPER Critic Repair", color="#0f766e")

    ax2.set_ylim(0, 1.12)
    ax2.set_ylabel("Official BixBench3 Table Score", fontsize=10, fontweight="bold")
    ax2.set_title("B. Before vs. After POPPER Sequential Falsification (12/13 Repaired)", fontsize=11.5, fontweight="bold", pad=10)
    ax2.set_xticks(xb)
    ax2.set_xticklabels(labels_b, fontsize=8.8)
    ax2.grid(axis="y", linestyle=":", alpha=0.6)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.legend(loc="upper right", fontsize=8.2, frameon=True)

    for b in bars_r1:
        h = b.get_height()
        ax2.text(b.get_x() + b.get_width() / 2, h + 0.018, f"{h:.2f}", ha="center", va="bottom", fontsize=8.2, fontweight="bold", color="#991b1b" if h == 0 else "#374151")
    for b in bars_r2:
        h = b.get_height()
        ax2.text(b.get_x() + b.get_width() / 2, h + 0.018, f"{h:.2f}", ha="center", va="bottom", fontsize=8.2, fontweight="bold", color="#0f766e")

    plt.tight_layout()
    fig.savefig(FIGS / "bixbench3_ablation_results.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    build_swarm_illustration()
    build_ablation_chart()
    print("Generated figs/popper_swarm_illustration.png and figs/bixbench3_ablation_results.png")
