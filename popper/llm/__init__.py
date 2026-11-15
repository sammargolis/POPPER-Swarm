"""LLM client abstractions for POPPER (OpenAI, Anthropic, SGLang, vLLM, llama.cpp)."""

from __future__ import annotations

from typing import Any, Optional


class CustomLLMClient:
    """OpenAI-compatible client supporting both frontier APIs and local inference servers."""

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20240620",
        is_locally_served: bool = False,
        server_port: Optional[int] = None,
        api_key: str = "EMPTY",
    ) -> None:
        self.model = model
        self.is_locally_served = is_locally_served
        self.server_port = server_port
        self.api_key = api_key

    @property
    def base_url(self) -> Optional[str]:
        if self.is_locally_served and self.server_port:
            return f"http://localhost:{self.server_port}/v1"
        return None
