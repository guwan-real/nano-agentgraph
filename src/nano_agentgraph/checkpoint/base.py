"""Checkpoint interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Checkpoint:
    """A future checkpoint record shape."""

    thread_id: str
    step: int
    next_node: str | None
    state: dict[str, Any]
    interrupted: bool = False
    interrupt_payload: Any | None = None


class BaseCheckpointSaver:
    """Base checkpoint saver interface."""

    def get_latest(self, thread_id: str) -> Checkpoint | None:
        """Return the latest checkpoint for a thread."""
        raise NotImplementedError

    def put(self, thread_id: str, checkpoint: Checkpoint) -> None:
        """Store a checkpoint for a thread."""
        raise NotImplementedError

    def list(self, thread_id: str) -> list[Checkpoint]:
        """List checkpoints for a thread."""
        raise NotImplementedError
