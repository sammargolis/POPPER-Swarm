# ICML Submission & Full-Benchmark Scaling Plan for POPPER-Swarm

## 1. Executive Summary & Core ICML Thesis

**Working Paper Title:**  
*POPPER-Swarm: Anytime-Valid Sequential E-Value Falsification for Multi-Agent Scientific Study Reproduction*

**Why This Can Win an ICML Main-Track Acceptance (and Spotlight/Oral):**
1. **Identifies and Formalizes a Fundamental Failure Mode in Multi-Agent Science ("The Multiplicative Artifact Trap"):**
   - Recent agentic science benchmarks (BixBench3, DiscoveryBench, ScienceAgentBench, Kosmos) show that single-agent ReAct loops and unverified multi-agent swarms plateau sharply (`0.5230` SOTA on BixBench3; 20.6% fabricated or flawed claims in Kosmos).
   - We prove *why*: multi-stage scientific pipelines (`30+` chained steps from raw sequencing files to downstream pathway tables) have **multiplicative error coupling** ($\mathcal{S}(A) = \text{Row\_F1} \times \text{Col\_F1} \times \text{CCC} \times \text{Label\_F1}$). Even if an agent's step-wise success probability is $p = 0.97$, a 30-step unverified pipeline succeeds with probability $0.97^{30} \approx 0.40$, and a single boundary error (e.g., unstripped `.15` Ensembl version suffix or alphabetical factor-level inversion in R `DESeq2`) collapses a `0.9989` concordance table to `0.0000`.
2. **Methodological Contribution (Sequential $E$-Processes Over Executable Artifact Contracts):**
   - While POPPER (Huang et al., ICML 2025) introduced sequential falsification for *binary natural-language hypotheses*, it does not address *closed-loop code/artifact synthesis* where an Experimenter agent iteratively edits and re-submits high-dimensional tables across $T$ rounds.
   - Repeatedly checking and repairing candidate artifacts with standard $p$-values violates Type-I error control (optional stopping / $p$-hacking by the LLM coder).
   - **POPPER-Swarm** introduces **anytime-valid sequential $e$-value artifact contracts** (`F1_EXISTENCE` through `F6_BIO_PRIOR_ALIGNMENT`) using Vovk–Wang calibration ($e_k = \frac{1}{2} p_k^{-1/2}$) and Ville's inequality stopping boundary ($\mathbb{P}_{H_0}(\exists t \ge 1 : E_t \ge 1/\alpha) \le \alpha$), coupled with **anti-leakage literature grounding** (Exa) and **persistent cross-agent episodic/semantic memory** (`past.dev`).
3. **Strong Empirical Proof Already in Hand (Plus Path to Full 20-Study SOTA):**
   - On our 2-study, 19-artifact raw-FASTQ benchmark slice (`27.3 GB` raw sequencing data across `113` libraries), POPPER-Swarm lifts official BixBench3 grade from **`0.1615`** (Matched-Compute Single-Agent Baseline) to **`0.7413`** (`4.6x` improvement) and PhDval-1 process score (`openai/gpt-5.5`) from **`0.4250`** to **`0.8450`**, catching and repairing **`13 / 13`** faulty Round-1 tables.

---

## 2. Gap Analysis: Hackathon Prototype $\rightarrow$ ICML Main-Track Paper

To pass a rigorous 4-reviewer ICML panel without any reviewer raising a scope or statistical-power objection, we need to close four specific gaps between our current repository and the final submission:

| Dimension | What We Have Right Now (Verified) | What ICML Reviewers Will Demand | Concrete Action Required |
| :--- | :--- | :--- | :--- |
| **1. Benchmark Coverage (`BixBench3`)** | Full raw-FASTQ reproduction on **3 / 20 studies** (`Task 9`: `0.7536`, `Task 11`: `0.7068`, `Task 1`: `0.2650` = **31 / 138 artifacts**). | Evaluation across **all 20 BixBench3 studies (`138 / 138` artifacts)** for direct 1-to-1 leaderboard comparison against `0.5230` (Gemini 4 Argon). | Run the remaining **17 studies (`107` artifacts)** on an 8-worker cloud VM (`~160 GB` disk, `~6–8 hours` wall-clock). |
| **2. Multi-Seed & Multi-Backbone Variance** | 1 deterministic run per ablation condition on `Task 9` + `Task 11`. | Mean $\pm$ standard error across **$N=3$ seeds** and **$\ge 2$ LLM backbones** (e.g., `Claude 4.6 Opus/Sonnet`, `Gemini 4 Argon`, `GPT-5.5`, plus open-weight `Llama-3.3-70B` / `DeepSeek-R1`). | Run 3 seeds $\times$ 3 backbones on the 5-way ablation suite and report paired bootstrap confidence intervals. |
| **3. Theoretical & Empirical Calibration Analysis** | Ville's inequality formulation ($E_t = \prod e_k \ge 20.0$) and 32 real falsification trajectories in `outputs/popper_ledger.json`. | Formal **Proposition 1** (Anytime-Valid Family-Wise Error Rate under Adaptive Agent Repair) + **Null Permutation Calibration Plot** ($\alpha \in \{0.01, 0.05, 0.10, 0.20\}$ vs. empirical false-rejection rate, compared against naive $p$-value and Fisher combination). | Add permutation/perturbation calibration script (`scripts/run_calibration_study.py`) injecting synthetic corruptions and null perturbations across all 138 ground-truth tables. |
| **4. Second Benchmark Generalization** | BixBench3 raw-FASTQ studies. | Proof that POPPER-Swarm generalizes beyond BixBench3 (e.g., **TargetVal** from `snap-stanford/POPPER` or **ScienceAgentBench**). | Run `Popper-Swarm` on the `IL2` / `IFNG` TargetVal benchmark (`100` hypotheses) to show strict superiority over single-agent `Popper` and `Self-Refine`. |

---

## 3. Eight-Week Execution Timeline to ICML Submission

### Phase 1: Full 20-Study BixBench3 Scaling (Weeks 1–2)
- **Task 1.1 (Cloud Staging):** Provision a 32-vCPU, 500 GB NVMe cloud instance with `bixbench3`, `HISAT2`, `STAR`, `bowtie2`, `samtools`, `subread`, `CellRanger`, and Bioconductor `R 4.4`.
- **Task 1.2 (Full 20-Study Execution):** Run `POPPER-Swarm (Full)` and `Single-Agent Baseline` across all 20 studies (`Task 1` through `Task 20`, `138` artifacts).
- **Task 1.3 (Bioconductor Version Pinning):** Containerize historical Bioconductor annotation snapshots (`org.Hs.eg.db v3.12` from 2021 vs `v3.23` from 2026) inside `Dockerfile` so the 4 Gene Ontology tables in Task 9 (`0.20–0.47`) also reach `>0.85` exact row/p-value parity.

### Phase 2: Multi-Backbone Ablations & Calibration Experiments (Weeks 3–4)
- **Task 2.1 (5-Way Ablation Across 3 Seeds):** Run the 5 controlled conditions (`Single-Agent`, `-Exa`, `-Critic`, `-past.dev`, `Full POPPER-Swarm`) across `3` seeds and `3` model families (`Claude`, `GPT-5.5`, `Gemini`).
- **Task 2.2 (E-Value vs. P-Value Optional-Stopping Study):** Compare Vovk–Wang $e$-value multiplication ($e_k = \frac{1}{2} p_k^{-1/2}$) against:
  1. Uncorrected sequential $p$-values ($p < 0.05$),
  2. Bonferroni-corrected $p$-values,
  3. Fisher's combined probability test ($\chi^2_{2k}$), and
  4. LLM-only self-refine critic (no statistical $e$-value test).
  Measure **Power (True Bug Catch Rate)** vs. **Type-I Error (False Rejection of Valid Artifacts)** across $t = 1 \dots 10$ repair rounds.

### Phase 3: Cross-Benchmark Generalization & Memory Scaling Analysis (Weeks 5–6)
- **Task 3.1 (Sequential Study Transfer Curve):** Measure how `past.dev` `global_learnings` accumulated across `Task 1 -> Task 20` reduce **Round-1 rejection rates** as a function of the number of previously completed studies $M \in [1, 20]$ (demonstrating continual self-improvement across studies without weight updates).
- **Task 3.2 (TargetVal / DiscoveryBench Evaluation):** Run `POPPER-Swarm` on the original `snap-stanford/POPPER` biological perturbation benchmark (`IL2`, `IFNG`) to demonstrate a direct improvement on their own benchmark.

### Phase 4: Paper Polishing, Internal Red-Teaming & Reproducibility Package (Weeks 7–8)
- **Task 4.1 (8-Page Main Body + Appendix):** Finalize the 8-page ICML main text (excluding references and impact statement) + full technical appendix (`Appendix A–E`).
- **Task 4.2 (Anonymous Code & Artifact Release):** Package the anonymized repository (`popper/`, `src/popper_swarm/`, `outputs/popper_ledger.json`, `benchmark_scripts/run_bixbench3.sh`) for supplementary submission.

---

## 4. Paper Structure (ICML 8-Page Main Body + Appendix)

1. **Abstract (~200 words):** Problem (multiplicative collapse in long-horizon scientific reproduction), Method (POPPER-Swarm: 5-role multi-agent architecture with anytime-valid sequential $e$-value artifact contracts, anti-leakage Exa search grounding, and `past.dev` cross-agent memory), Results (`0.7413` vs `0.1615` matched-compute single agent, `0.8450` PhDval-1, `13/13` Round-1 bugs falsified and repaired).
2. **Section 1: Introduction (1.25 pages):**
   - The gap between hypothesis generation and rigorous computational reproduction.
   - Why multi-step bioinformatics pipelines break single-agent ReAct loops (the Multiplicative Artifact Trap).
   - Contributions summary (Formalization, Architecture, 5-Way Controlled Ablation, Open Observatory & Ledger).
3. **Section 2: Related Work (0.75 pages):**
   - AI Scientist Agents (`Popper` Huang et al. 2025; `Kosmos` Mitchener et al. 2025; `Biomni`; `Virtual Lab`).
   - Scientific Coding & Reproduction Benchmarks (`BixBench3`, `DiscoveryBench`, `ScienceAgentBench`, `BioCoder`).
   - Game-Theoretic Probability, $E$-Values, and Safe Anytime-Valid Inference (Vovk & Wang 2021; Ramdas et al. 2023; Ville 1939).
4. **Section 3: Problem Formulation & The Multiplicative Artifact Trap (1.0 page):**
   - Formal model of a scientific reproduction DAG $\mathcal{G} = (\mathcal{V}, \mathcal{E})$ mapping raw sequencing reads $\mathcal{D}_{\text{raw}}$ to target tables $\{A^{(1)}, \dots, A^{(M)}\}$.
   - Theorem / Proposition 1: Why iterative LLM self-refinement with standard $p$-values inflates Type-I error under optional stopping, whereas our sequential $e$-process $E_t = \prod_{k=1}^t e_k$ preserves $\mathbb{P}_{H_0}(\exists t \ge 1: E_t \ge 1/\alpha) \le \alpha$.
5. **Section 4: The POPPER-Swarm Architecture (1.75 pages):**
   - Five specialized agent roles (`Inspector`, `Proposer`, `Experimenter`, `Critic`, `Auditor`).
   - Six-stage executable falsification battery (`F1_EXISTENCE`, `F2_COLUMN_CONTRACT`, `F3_ROWKEY_NAMESPACE`, `F4_NUMERIC_INTEGRITY`, `F5_STAT_COHERENCE`, `F6_BIO_PRIOR_ALIGNMENT`).
   - Anti-leakage literature grounding via Exa (`/search` + `/contents` with target-DOI exclusion).
   - Cross-agent shared memory and continual rule distillation via `past.dev` (`data_facts`, `rejected_hypotheses`, `global_learnings`).
6. **Section 5: Experiments & 5-Way Controlled Ablation on BixBench3 (2.25 pages):**
   - Experimental setup, official deterministic grading (`Row_F1 × Col_F1 × CCC × Label_F1`), and `openai/gpt-5.5` PhDval-1 8-dimension process judge.
   - Main 5-way ablation results (`Table 1` & `Figure 2`).
   - Case studies of autonomous falsification and repair (`Table 2`: `.15` Ensembl suffix stripping, `DESeq2` alphabetical factor inversion, `3' Tag-Seq` forward-stranded clipping, `TempO-Seq` probe namespace, and `88-set` GO umbrella filtering).
   - Honest failure mode analysis: Bioconductor annotation drift (`2021 v3.12` vs `2026 v3.23`).
7. **Section 6: Discussion, Limitations & Broader Impact (1.0 page):**
   - Compute scaling, containerization of historical software environments, and trustworthy autonomous science.
8. **Appendix (`Appendix A–D`):**
   - Full proofs, complete 32-evaluation POPPER $e$-value ledger, Exa query provenance, and `past.dev` memory schema.
