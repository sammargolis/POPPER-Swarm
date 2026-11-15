"""Sequential E-Value Falsification Engine (Popper, Huang et al., ICML 2025).

Implements anytime-valid sequential hypothesis testing with Type-I error control
for computational biology artifact validation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class FalsificationTestResult:
    """Result of a single falsification sub-experiment on a candidate artifact."""

    test_id: str
    artifact_id: str
    hypothesis_statement: str
    null_implication_tested: str
    passed: bool
    e_value: float
    p_value_equivalent: float
    observed_statistic: str
    expected_contract: str
    remediation_prescription: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat().replace("+00:00", "Z"))


@dataclass(slots=True)
class ArtifactFalsificationLedger:
    """Tracks sequential e-process accumulation for an artifact across rounds."""

    artifact_id: str
    round_index: int
    alpha: float = 0.05
    tests: list[FalsificationTestResult] = field(default_factory=list)

    @property
    def cumulative_e_value(self) -> float:
        """Product/mean e-process accumulator under sequential falsification.

        In our Popperian setup, the null hypothesis H_0 is that the candidate artifact
        is a valid, contract-compliant reproduction of the biological method.
        Evidence *against* H_0 (i.e., evidence of a bug, sign flip, ID mismatch, or
        statistical anomaly) yields e_k >> 1. By Ville's inequality, if E_t >= 1/alpha,
        we reject the candidate artifact at level alpha.
        """
        if not self.tests:
            return 1.0
        # Product of independent/sequential e-values bounded to avoid float overflow
        prod = 1.0
        for t in self.tests:
            prod = min(1e9, prod * max(0.1, t.e_value))
        return round(prod, 4)

    @property
    def rejected(self) -> bool:
        threshold = 1.0 / self.alpha  # 20.0 for alpha = 0.05
        return self.cumulative_e_value >= threshold or any(not t.passed for t in self.tests)

    @property
    def failed_tests(self) -> list[FalsificationTestResult]:
        return [t for t in self.tests if not t.passed]

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "round_index": self.round_index,
            "alpha": self.alpha,
            "rejection_threshold_e": round(1.0 / self.alpha, 2),
            "cumulative_e_value": self.cumulative_e_value,
            "decision": "REJECTED" if self.rejected else "ACCEPTED",
            "tests_run": len(self.tests),
            "tests_failed": len(self.failed_tests),
            "tests": [
                {
                    "test_id": t.test_id,
                    "hypothesis_statement": t.hypothesis_statement,
                    "null_implication_tested": t.null_implication_tested,
                    "passed": t.passed,
                    "e_value": t.e_value,
                    "p_value_equivalent": t.p_value_equivalent,
                    "observed_statistic": t.observed_statistic,
                    "expected_contract": t.expected_contract,
                    "remediation_prescription": t.remediation_prescription,
                    "timestamp": t.timestamp,
                }
                for t in self.tests
            ],
        }


def p_to_calibrated_e_value(p_value: float) -> float:
    """Convert a p-value against validity into a Vovk-Wang calibrated e-value:
    e(p) = 0.5 * (p ** -0.5) for p in (0, 1].
    When p -> 0 (strong refutation), e -> +infinity.
    When p >= 0.25 (consistent with validity), e <= 1.0.
    """
    p_clamped = max(1e-8, min(1.0, float(p_value)))
    return round(0.5 * math.pow(p_clamped, -0.5), 4)
