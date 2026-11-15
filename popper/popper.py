"""Core Popper class for automated hypothesis and study validation via sequential falsification."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from popper.agent import SequentialFalsificationTest
from popper.utils import (
    BixBench3DataLoader,
    CustomDataLoader,
    DiscoveryBenchDataLoader,
    ExperimentalDataLoader,
)


class Popper:
    """Wrapper class for hypothesis validation using sequential falsification testing."""

    def __init__(
        self,
        llm: str = "claude-3-5-sonnet-20240620",
        is_locally_served: bool = False,
        server_port: Optional[int] = None,
        api_key: str = "EMPTY",
        **kwargs: Any,
    ) -> None:
        """Initialize Popper.

        Args:
            llm (str): Name of the LLM model to use
            is_locally_served (bool): Whether to route to a local OpenAI-compatible server
            server_port (Optional[int]): Port for locally served LLM (vLLM, SGLang, llama.cpp)
            api_key (str): API key for local or remote server
            **kwargs: Additional arguments to pass to SequentialFalsificationTest
        """
        self.llm = llm
        self.agent: Optional[SequentialFalsificationTest] = None
        self.data_loader: Any = None
        self.data_path: Optional[str] = None
        self.is_local = is_locally_served
        self.port = server_port
        self.api_key = api_key
        self.kwargs = kwargs

    def register_data(
        self,
        data_path: str,
        data_sampling: int = -1,
        loader_type: str = "bio",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register data for hypothesis testing.

        Args:
            data_path (str): Path to data directory
            data_sampling (int): Number of datasets to sample (-1 for all)
            loader_type (str): Type of data loader ('bio', 'bixbench3', 'custom', or 'discovery_bench')
            metadata (Optional[Dict]): Metadata required for DiscoveryBenchDataLoader or BixBench3
        """
        if not os.path.exists(data_path):
            os.makedirs(data_path, exist_ok=True)

        self.data_path = data_path
        if loader_type in ("bio", "bio_selected"):
            self.data_loader = ExperimentalDataLoader(
                data_path=data_path,
                table_dict_selection="all_bio" if loader_type == "bio" else "default",
                data_sampling=data_sampling,
            )
        elif loader_type == "bixbench3":
            self.data_loader = BixBench3DataLoader(data_path=data_path, metadata=metadata or {})
        elif loader_type == "custom":
            self.data_loader = CustomDataLoader(data_folder=data_path)
        elif loader_type == "discovery_bench":
            if metadata is None:
                raise ValueError("Metadata must be provided for DiscoveryBenchDataLoader")
            self.data_loader = DiscoveryBenchDataLoader(data_path=data_path, metadata=metadata)
        else:
            raise ValueError(f"Unknown loader_type: {loader_type}")

    def configure(
        self,
        alpha: float = 0.05,
        aggregate_test: str = "E-value",
        max_num_of_tests: int = 6,
        max_retry: int = 3,
        time_limit: float = 2.0,
        relevance_checker: bool = True,
        use_react_agent: bool = True,
        use_exa_search: bool = True,
        use_past_memory: bool = True,
    ) -> None:
        """Configure the sequential falsification test parameters.

        Args:
            alpha (float): Significance level (Type-I error bound; Ville threshold = 1 / alpha)
            aggregate_test (str): Test aggregation method ('E-value' or 'Fisher')
            max_num_of_tests (int): Maximum number of falsification tests to run
            max_retry (int): Maximum number of retries for failed tests
            time_limit (float): Time limit in hours
            relevance_checker (bool): Whether to use relevance checker
            use_react_agent (bool): Whether to use ReAct execution agent
            use_exa_search (bool): Whether to ground method/marker checks via Exa search
            use_past_memory (bool): Whether to persist/recall state via past.dev shared memory
        """
        self.agent = SequentialFalsificationTest(
            llm=self.llm,
            is_locally_served=self.is_local,
            server_port=self.port,
            api_key=self.api_key,
            data_loader=self.data_loader,
            alpha=alpha,
            aggregate_test=aggregate_test,
            max_num_of_tests=max_num_of_tests,
            max_retry=max_retry,
            time_limit=time_limit,
            relevance_checker=relevance_checker,
            use_react_agent=use_react_agent,
            use_exa_search=use_exa_search,
            use_past_memory=use_past_memory,
            **self.kwargs,
        )

    def validate(
        self,
        hypothesis: str,
        artifact_path: Optional[str | Path] = None,
        contract: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Validate a scientific hypothesis or reproduced bioinformatics artifact.

        Args:
            hypothesis (str): Free-form hypothesis or artifact reproduction claim
            artifact_path (Optional[str | Path]): Optional path to candidate CSV/TSV table
            contract (Optional[Dict[str, Any]]): Optional falsification contract specification

        Returns:
            Dict[str, Any]: Structured validation result with e-value trajectory and conclusion
        """
        if self.agent is None:
            self.configure()
        assert self.agent is not None
        return self.agent.run(
            hypothesis=hypothesis,
            artifact_path=artifact_path,
            contract=contract,
        )
