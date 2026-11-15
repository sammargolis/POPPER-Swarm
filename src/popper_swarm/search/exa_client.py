"""Exa Search & Grounding Client following canonical `build-with-exa` patterns."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from exa_py import Exa

# Verbatim objective parameter description required by the canonical build-with-exa skill:
EXA_OBJECTIVE_DESCRIPTION = (
    "Goal for this search turn; say which documents should rank first, "
    "which should be excluded, and what specific facts or figures to pull from them."
)

# System prompt guidance for LLMs equipped with Exa web search as a tool:
EXA_LLM_SYSTEM_PROMPT_GUIDANCE = """
## Exa Web Search Tool Guidance
You have access to `exa_search` and `exa_get_contents` to search the live web and retrieve methodological documentation, package parameter specifications, error troubleshooting, and canonical biological reference facts beyond your training data.
- On every `exa_search` call, provide both a natural-language `query` (retrieval intent only—never put keep/drop rules like 'only' or 'exclude' in `query`) and a detailed `objective` stating which documents should rank first (e.g., Bioconductor vignettes, GitHub tool repositories, official CLI manuals, peer-reviewed pathway references), which should be excluded, and what specific parameters, flags, or biological markers to pull.
- Never search for the benchmark target study's own title, DOI, author list, or precomputed answer tables. Use Exa strictly for legitimate methodological grounding, package usage, and independent biological falsification priors.
""".strip()


@dataclass(slots=True)
class ExaSearchRecord:
    """Structured provenance record for a single Exa API call."""

    timestamp: str
    agent_role: str
    endpoint: str
    query: str
    objective: str
    request_id: str | None
    latency_ms: float
    results: list[dict[str, Any]]
    sanitized_terms: list[str]


class ExaResearchClient:
    """Canonical Exa API client (`exa-py`) with BixBench3 anti-leakage sanitization and provenance logging.

    Follows `build-with-exa` skill rules:
    - Uses `exa.search(query, objective=objective, type="auto", contents={"highlights": True})`
      without unnecessary boilerplate (`numResults`, `category`, `maxAgeHours`, or stacked content fields).
    - Supports `output_schema` + `system_prompt` when structured extraction is needed.
    - Supports `exa.get_contents(urls, highlights=True)` with top-level content fields and `statuses` inspection.
    - Enforces benchmark integrity by stripping target-paper DOIs or blocked answer URLs before calling Exa
      and filtering any result matching the target paper's DOI.
    """

    def __init__(
        self,
        api_key: str,
        provenance_log_path: Path | None = None,
        blocked_identifiers: list[str] | None = None,
        enabled: bool = True,
    ) -> None:
        self.api_key = api_key
        self.provenance_log_path = provenance_log_path
        self.blocked_identifiers = [b.lower() for b in (blocked_identifiers or []) if b]
        self.enabled = enabled and bool(api_key)
        self._exa = Exa(api_key=api_key) if self.enabled else None

    def tool_definitions_anthropic(self) -> list[dict[str, Any]]:
        """Return canonical Anthropic tool definitions for `exa_search` and `exa_get_contents`."""
        return [
            {
                "name": "exa_search",
                "description": (
                    "Search the live web and return the most relevant URLs and content. "
                    "Use for fresh information, bioinformatics tool manuals, Bioconductor/PyPI docs, "
                    "and canonical biological markers beyond the model's training data."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "objective": {
                            "type": "string",
                            "description": EXA_OBJECTIVE_DESCRIPTION,
                        },
                    },
                    "required": ["query", "objective"],
                },
            },
            {
                "name": "exa_get_contents",
                "description": (
                    "Extract clean highlights from known URLs (such as documentation pages or "
                    "GitHub READMEs discovered in prior steps)."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "urls": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of exact HTTP/HTTPS URLs to extract highlights from.",
                        },
                    },
                    "required": ["urls"],
                },
            },
        ]

    def search(
        self,
        query: str,
        *,
        objective: str,
        agent_role: str = "swarm",
        system_prompt: str | None = None,
        output_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run canonical Exa `/search` with `type='auto'` and `contents={'highlights': True}`."""
        clean_query, removed = self._sanitize_query(query)
        now_iso = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        if not self.enabled or self._exa is None:
            return {"enabled": False, "query": clean_query, "results": []}

        t0 = time.perf_counter()
        kwargs: dict[str, Any] = {
            "type": "auto",
            "objective": objective,
            "contents": {"highlights": True},
        }
        if system_prompt is not None:
            kwargs["system_prompt"] = system_prompt
        if output_schema is not None:
            kwargs["output_schema"] = output_schema

        response = self._exa.search(clean_query, **kwargs)
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        parsed_results: list[dict[str, Any]] = []
        for item in getattr(response, "results", []) or []:
            url = getattr(item, "url", "") or ""
            title = getattr(item, "title", "") or ""
            if self._is_blocked_result(url, title):
                continue
            highlights = getattr(item, "highlights", None) or []
            parsed_results.append(
                {
                    "title": title,
                    "url": url,
                    "published_date": getattr(item, "published_date", None),
                    "highlights": list(highlights)[:3],
                }
            )

        structured_output = None
        raw_output = getattr(response, "output", None)
        if raw_output is not None:
            structured_output = {
                "content": getattr(raw_output, "content", None),
                "grounding": getattr(raw_output, "grounding", None),
            }

        payload = {
            "endpoint": "/search",
            "timestamp": now_iso,
            "agent_role": agent_role,
            "query": clean_query,
            "objective": objective,
            "request_id": getattr(response, "request_id", None),
            "latency_ms": latency_ms,
            "sanitized_terms": removed,
            "results": parsed_results,
            "output": structured_output,
        }
        self._append_provenance(payload)
        return payload

    def get_contents(
        self,
        urls: list[str],
        *,
        agent_role: str = "swarm",
    ) -> dict[str, Any]:
        """Run canonical Exa `/contents` with top-level `highlights=True` and inspect `statuses`."""
        now_iso = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        safe_urls = [u for u in urls if not self._is_blocked_result(u, "")]
        if not self.enabled or self._exa is None or not safe_urls:
            return {"enabled": False, "urls": safe_urls, "results": [], "statuses": []}

        t0 = time.perf_counter()
        # Per build-with-exa references/contents.md: top-level `highlights=True` (NOT nested inside contents)
        response = self._exa.get_contents(safe_urls, highlights=True)
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        statuses = []
        for st in getattr(response, "statuses", []) or []:
            statuses.append(
                {
                    "id": getattr(st, "id", None),
                    "status": getattr(st, "status", None),
                    "error": getattr(st, "error", None),
                }
            )

        parsed_results = []
        for item in getattr(response, "results", []) or []:
            url = getattr(item, "url", "") or ""
            title = getattr(item, "title", "") or ""
            if self._is_blocked_result(url, title):
                continue
            parsed_results.append(
                {
                    "title": title,
                    "url": url,
                    "highlights": list(getattr(item, "highlights", None) or []),
                }
            )

        payload = {
            "endpoint": "/contents",
            "timestamp": now_iso,
            "agent_role": agent_role,
            "urls": safe_urls,
            "request_id": getattr(response, "request_id", None),
            "latency_ms": latency_ms,
            "statuses": statuses,
            "results": parsed_results,
        }
        self._append_provenance(payload)
        return payload

    def _sanitize_query(self, query: str) -> tuple[str, list[str]]:
        removed: list[str] = []
        cleaned = query
        for term in self.blocked_identifiers:
            if term and term in cleaned.lower():
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                cleaned = pattern.sub("", cleaned)
                removed.append(term)
        # Strip raw DOI patterns (10.xxxx/...)
        doi_matches = re.findall(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", cleaned)
        for m in doi_matches:
            cleaned = cleaned.replace(m, "")
            removed.append(m)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned or "computational biology bioinformatics analysis vignette", removed

    def _is_blocked_result(self, url: str, title: str) -> bool:
        haystack = f"{url} {title}".lower()
        if "bixbench3-ground-truth" in haystack:
            return True
        return any(term in haystack for term in self.blocked_identifiers if len(term) >= 6)

    def _append_provenance(self, record: dict[str, Any]) -> None:
        if self.provenance_log_path is None:
            return
        self.provenance_log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.provenance_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
