"""Inspect AI @solver integration for POPPER-Swarm on BixBench3."""

from __future__ import annotations

import os
from inspect_ai.agent import Agent, react
from inspect_ai.model import CompactionAuto
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.tool import Tool, bash_session, python, text_editor, tool

from bixbench3.inspect_harness.tools import request_web_access

from .config import SwarmConfig
from .falsification import run_popper_falsification_battery
from .memory import PastMemoryClient
from .search import EXA_LLM_SYSTEM_PROMPT_GUIDANCE, EXA_OBJECTIVE_DESCRIPTION, ExaResearchClient


@tool
def exa_search() -> Tool:
    async def execute(query: str, objective: str) -> str:
        """Search the live web using Exa and return relevant URLs and highlights.

        Use for fresh information, bioinformatics tool manuals, Bioconductor/PyPI
        documentation, and canonical biological reference facts beyond model training data.

        Args:
            query: Natural-language retrieval intent (no keep/drop rules).
            objective: Goal for this search turn; say which documents should rank first, which should be excluded, and what specific facts or figures to pull from them.
        """
        client = ExaResearchClient(api_key=os.environ.get("EXA_API_KEY", ""))
        result = client.search(query, objective=objective, agent_role="inspect_solver")
        import json
        return json.dumps(result, ensure_ascii=False)

    return execute


@tool
def past_memory_share() -> Tool:
    async def execute(
        action: str,
        agent_identity: str,
        content_or_query: str,
        category: str = "fact",
    ) -> str:
        """Read from or write to the shared past.dev multi-agent memory layer.

        Args:
            action: Either 'ingest' (write a fact/hypothesis/rejection) or 'recall' (query shared memory).
            agent_identity: Role identity ('proposer', 'inspector', 'experimenter', 'critic', 'auditor').
            content_or_query: Text to ingest or natural-language query to recall.
            category: Category tag when ingesting ('plan', 'data_facts', 'candidates', 'rejected_hypotheses', 'verified_artifacts', 'global_learnings').
        """
        import json
        client = PastMemoryClient(api_key=os.environ.get("PAST_API_KEY", ""))
        role = agent_identity if agent_identity in ("proposer", "inspector", "experimenter", "critic", "auditor") else "experimenter"
        if action == "ingest":
            res = client.ingest(
                author=role,  # type: ignore[arg-type]
                task_id=os.environ.get("BIXBENCH3_TASK_ID", "bixbench3"),
                category=category,
                label=f"{role}:{category}",
                content=content_or_query,
            )
            return json.dumps(res)
        rec = client.recall(
            reader=role,  # type: ignore[arg-type]
            query=content_or_query,
        )
        return json.dumps(rec[:8], ensure_ascii=False)

    return execute


@solver
def popper_swarm_agent() -> Agent:
    """Drop-in Inspect AI replacement for `bixbench3_agent()` equipped with Exa,
    `past.dev` shared memory, and POPPER sequential falsification directives.
    """
    return react(
        prompt=EXA_LLM_SYSTEM_PROMPT_GUIDANCE,
        tools=[
            bash_session(timeout=600),
            python(timeout=600),
            text_editor(timeout=120),
            request_web_access(),
            exa_search(),
            past_memory_share(),
        ],
        compaction=CompactionAuto(),
    )
