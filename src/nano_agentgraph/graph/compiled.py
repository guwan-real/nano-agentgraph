"""Compiled sequential graph runtime."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any

from nano_agentgraph.errors import InvalidUpdateError
from nano_agentgraph.graph.constants import END, START
from nano_agentgraph.types import Command


class CompiledStateGraph:
    """A compiled graph that executes one static node chain."""

    def __init__(
        self,
        nodes: dict[str, Callable[[dict[str, Any]], Any]],
        edges: dict[str, list[str]],
    ) -> None:
        self._nodes = nodes
        self._edges = edges

    def invoke(
        self,
        input: dict[str, Any] | Command,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run the graph to END and return the final state."""

        del config
        if isinstance(input, Command):
            msg = "Command input is not implemented yet; it is planned for M3/M5."
            raise NotImplementedError(msg)
        if not isinstance(input, dict):
            msg = "invoke(input) expects a state dictionary."
            raise TypeError(msg)

        state = dict(input)
        current = self._next_node(START)

        while current != END:
            update = self._nodes[current](state)
            if isinstance(update, Command):
                msg = "Command node returns are not implemented yet; planned for M3."
                raise NotImplementedError(msg)
            if not isinstance(update, dict):
                msg = (
                    f"Node {current!r} returned {type(update).__name__}; "
                    "nodes must return a dict update in M1."
                )
                raise InvalidUpdateError(msg)
            state.update(update)
            current = self._next_node(current)

        return state

    def stream(
        self,
        input: dict[str, Any] | Command,
        config: dict[str, Any] | None = None,
        *,
        stream_mode: str = "values",
        version: str = "v2",
    ) -> Iterator[dict[str, Any]]:
        """Stream graph execution events.

        Streaming is part of a later milestone.
        """

        del input, config, stream_mode, version
        msg = "stream() is not implemented yet; it is planned for M6."
        raise NotImplementedError(msg)

    def get_state(self, config: dict[str, Any]) -> Any:
        """Return saved graph state.

        Checkpoint state inspection is part of a later milestone.
        """

        del config
        msg = "get_state() is not implemented yet; it is planned for M4."
        raise NotImplementedError(msg)

    def update_state(
        self,
        config: dict[str, Any],
        values: dict[str, Any],
        as_node: str | None = None,
    ) -> Any:
        """Update saved graph state.

        Checkpoint state mutation is part of a later milestone.
        """

        del config, values, as_node
        msg = "update_state() is not implemented yet; it is planned for M4."
        raise NotImplementedError(msg)

    def _next_node(self, source: str) -> str:
        targets = self._edges[source]
        return targets[0]
