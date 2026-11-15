"""Utilities for POPPER ReAct execution traces."""

from __future__ import annotations

from typing import Any, Dict


def format_react_step(thought: str, action: str, observation: str) -> Dict[str, Any]:
    return {"thought": thought, "action": action, "observation": observation}
