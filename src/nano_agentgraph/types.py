"""LangGraph-style public runtime types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Command:
    """A small placeholder for LangGraph-style command returns.

    Command-based routing and resume behavior are planned for later milestones.
    """

    update: dict[str, Any] | None = None
    goto: str | None = None
    resume: Any | None = None


def interrupt(value: Any) -> Any:
    """Pause graph execution.

    Interrupt/resume semantics are intentionally not implemented in M0/M1.
    """

    del value
    msg = "interrupt() is not implemented yet; it is planned for M5."
    raise NotImplementedError(msg)
