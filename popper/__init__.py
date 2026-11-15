"""POPPER: Automated Hypothesis Validation with Agentic Sequential Falsifications."""

from popper.version import __version__
from popper.popper import Popper
from popper.agent import SequentialFalsificationTest

__all__ = ["Popper", "SequentialFalsificationTest", "__version__"]
