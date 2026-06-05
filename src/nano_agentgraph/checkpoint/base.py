"""Checkpoint interfaces reserved for later milestones."""

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
    """Base checkpoint saver placeholder for the M4 implementation."""

    def get_latest(self, thread_id: str) -> Checkpoint | None:
        """Return the latest checkpoint for a thread."""

        del thread_id
        msg = "Checkpoint saving is not implemented yet; it is planned for M4."
        raise NotImplementedError(msg)

    def put(self, thread_id: str, checkpoint: Checkpoint) -> None:
        """Store a checkpoint for a thread."""

        del thread_id, checkpoint
        msg = "Checkpoint saving is not implemented yet; it is planned for M4."
        raise NotImplementedError(msg)

    def list(self, thread_id: str) -> list[Checkpoint]:
        """List checkpoints for a thread."""

        del thread_id
        msg = "Checkpoint saving is not implemented yet; it is planned for M4."
        raise NotImplementedError(msg)
