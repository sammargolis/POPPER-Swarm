"""ReAct execution agent wrapper for POPPER sequential falsification."""

from __future__ import annotations

from typing import Any, Dict


class ReactAgent:
    """Executes Think -> Execute -> Observe falsification steps."""

    def __init__(self, llm: str = "claude-3-5-sonnet-20240620", **kwargs: Any) -> None:
        self.llm = llm
        self.kwargs = kwargs

    def invoke(self, prompt: str) -> Dict[str, Any]:
        return {"status": "ok", "llm": self.llm, "prompt": prompt}
