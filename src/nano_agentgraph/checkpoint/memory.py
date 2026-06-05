"""In-memory checkpoint saver."""

from __future__ import annotations

from copy import deepcopy

from nano_agentgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint


class InMemorySaver(BaseCheckpointSaver):
    """A small in-memory checkpoint saver keyed by thread ID."""

    def __init__(self) -> None:
        self._checkpoints: dict[str, list[Checkpoint]] = {}

    def get_latest(self, thread_id: str) -> Checkpoint | None:
        """Return the latest checkpoint for a thread."""

        checkpoints = self._checkpoints.get(thread_id, [])
        if not checkpoints:
            return None
        return deepcopy(checkpoints[-1])

    def put(self, thread_id: str, checkpoint: Checkpoint) -> None:
        """Store a checkpoint for a thread."""

        self._checkpoints.setdefault(thread_id, []).append(deepcopy(checkpoint))

    def list(self, thread_id: str) -> list[Checkpoint]:
        """List checkpoints for a thread."""

        return deepcopy(self._checkpoints.get(thread_id, []))
