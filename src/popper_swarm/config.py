"""Configuration and environment loading for POPPER-Swarm."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env", override=False)


@dataclass(slots=True)
class SwarmConfig:
    """Runtime configuration and ablation toggles for POPPER-Swarm."""

    exa_api_key: str = field(default_factory=lambda: os.environ.get("EXA_API_KEY", ""))
    past_api_key: str = field(default_factory=lambda: os.environ.get("PAST_API_KEY", ""))
    anthropic_api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))
    openai_api_key: str = field(default_factory=lambda: os.environ.get("OPENAI_API_KEY", ""))
    proposer_model: str = "claude-sonnet-4-6"
    inspector_model: str = "claude-sonnet-4-6"
    experimenter_model: str = "claude-sonnet-4-6"
    critic_model: str = "claude-sonnet-4-6"
    auditor_model: str = "claude-sonnet-4-6"
    enable_exa: bool = True
    enable_past_memory: bool = True
    enable_popper_critic: bool = True
    alpha_type1_error: float = 0.05
    max_falsification_rounds: int = 3
    workspace_dir: Path = field(default_factory=lambda: REPO_ROOT / "workspace")
    outputs_dir: Path = field(default_factory=lambda: REPO_ROOT / "outputs")
