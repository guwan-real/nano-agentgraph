"""LangGraph-style public runtime types."""

from __future__ import annotations

import json
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

from nano_agentgraph.errors import InterruptError

_NO_RESUME = object()


@dataclass(slots=True)
class _InterruptContext:
    resume: Any = _NO_RESUME
    used: bool = False


class _GraphInterrupt(Exception):
    def __init__(self, value: Any) -> None:
        super().__init__("Graph execution was interrupted.")
        self.value = value


_current_interrupt_context: ContextVar[_InterruptContext | None] = ContextVar(
    "nano_agentgraph_interrupt_context",
    default=None,
)


@dataclass(slots=True)
class Command:
    """A small LangGraph-style command object."""

    update: dict[str, Any] | None = None
    goto: str | None = None
    resume: Any | None = None


def interrupt(value: Any) -> Any:
    """Pause graph execution inside a node and return a resume value later."""

    context = _current_interrupt_context.get()
    if context is None:
        msg = "interrupt() can only be called while a graph node is executing."
        raise InterruptError(msg)

    if context.resume is not _NO_RESUME and not context.used:
        context.used = True
        return context.resume

    try:
        json.dumps(value)
    except (TypeError, ValueError) as exc:
        msg = "interrupt() payload must be JSON-serializable."
        raise InterruptError(msg) from exc

    raise _GraphInterrupt(value)
