"""Graph builder for the minimal sequential nano-agentgraph runtime."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from nano_agentgraph.errors import GraphValidationError
from nano_agentgraph.graph.compiled import CompiledStateGraph
from nano_agentgraph.graph.constants import END, START


class StateGraph:
    """Build a small LangGraph-style state graph.

    M1 supports a sequential chain of nodes connected by static edges. Advanced
    features such as checkpointing, interrupts, conditional routing, and Command
    routing deliberately raise clear errors until their milestones are added.
    """

    def __init__(self, state_schema: type[Any] | None = None) -> None:
        self.state_schema = state_schema
        self._nodes: dict[str, Callable[[dict[str, Any]], Any]] = {}
        self._edges: dict[str, list[str]] = {}

    def add_node(
        self,
        name_or_fn: str | Callable[[dict[str, Any]], Any],
        fn: Callable[[dict[str, Any]], Any] | None = None,
    ) -> StateGraph:
        """Add a node by explicit name or infer its name from the callable."""

        if fn is None:
            if isinstance(name_or_fn, str):
                msg = "add_node(name) requires a callable as the second argument."
                raise TypeError(msg)
            name = self._infer_node_name(name_or_fn)
            node_fn = name_or_fn
        else:
            if not isinstance(name_or_fn, str):
                msg = "add_node(fn, extra) is invalid; use add_node(name, fn)."
                raise TypeError(msg)
            name = name_or_fn
            node_fn = fn

        if name in {START, END}:
            msg = f"{name!r} is reserved and cannot be used as a node name."
            raise GraphValidationError(msg)
        if name in self._nodes:
            msg = f"Node {name!r} already exists."
            raise GraphValidationError(msg)
        if not callable(node_fn):
            msg = f"Node {name!r} must be callable."
            raise TypeError(msg)

        self._nodes[name] = node_fn
        return self

    def add_edge(self, source: str, target: str) -> StateGraph:
        """Add a static edge between START, nodes, and END."""

        if not isinstance(source, str) or not isinstance(target, str):
            msg = "add_edge(source, target) expects string node names."
            raise TypeError(msg)
        if source == END:
            msg = "END cannot be used as an edge source."
            raise GraphValidationError(msg)
        if target == START:
            msg = "START cannot be used as an edge target."
            raise GraphValidationError(msg)

        self._edges.setdefault(source, []).append(target)
        return self

    def set_entry_point(self, name: str) -> StateGraph:
        """Set the first node by adding an edge from START."""

        return self.add_edge(START, name)

    def set_finish_point(self, name: str) -> StateGraph:
        """Set a terminal node by adding an edge to END."""

        return self.add_edge(name, END)

    def add_conditional_edges(
        self,
        source: str,
        path: Callable[[dict[str, Any]], str],
        path_map: dict[str, str] | None = None,
    ) -> StateGraph:
        """Register conditional routing.

        Conditional edges are part of a later milestone.
        """

        del source, path, path_map
        msg = "add_conditional_edges() is not implemented yet; it is planned for M3."
        raise NotImplementedError(msg)

    def compile(
        self,
        checkpointer: Any | None = None,
        interrupt_before: Any | None = None,
        interrupt_after: Any | None = None,
        debug: bool = False,
    ) -> CompiledStateGraph:
        """Validate and compile the graph into an invokable runtime."""

        if checkpointer is not None:
            msg = "Checkpointing is not implemented yet; it is planned for M4."
            raise NotImplementedError(msg)
        if interrupt_before is not None or interrupt_after is not None:
            msg = "Interrupt controls are not implemented yet; they are planned for M5."
            raise NotImplementedError(msg)
        if debug:
            msg = "debug=True is not implemented yet."
            raise NotImplementedError(msg)

        self._validate()
        return CompiledStateGraph(
            nodes=dict(self._nodes),
            edges={source: list(targets) for source, targets in self._edges.items()},
        )

    @staticmethod
    def _infer_node_name(fn: Callable[[dict[str, Any]], Any]) -> str:
        name = getattr(fn, "__name__", None)
        if not name:
            msg = "Cannot infer a node name from this callable; use add_node(name, fn)."
            raise TypeError(msg)
        return name

    def _validate(self) -> None:
        if not self._edges.get(START):
            msg = "Graph must have an edge from START to an entry node."
            raise GraphValidationError(msg)

        for source, targets in self._edges.items():
            if source != START and source not in self._nodes:
                msg = f"Edge source {source!r} is not a known node."
                raise GraphValidationError(msg)
            if len(targets) > 1:
                msg = (
                    f"Node {source!r} has multiple outgoing edges. "
                    "Parallel routing is not implemented yet."
                )
                raise GraphValidationError(msg)
            for target in targets:
                if target != END and target not in self._nodes:
                    msg = f"Edge target {target!r} is not a known node."
                    raise GraphValidationError(msg)

        visited: set[str] = set()
        current = START

        while current != END:
            if current in visited:
                msg = f"Cycle detected at {current!r}; cycles are not supported in M1."
                raise GraphValidationError(msg)
            visited.add(current)

            targets = self._edges.get(current)
            if not targets:
                msg = f"Node {current!r} has no outgoing edge to continue or END."
                raise GraphValidationError(msg)
            current = targets[0]

        unreachable = set(self._nodes) - visited
        if unreachable:
            names = ", ".join(sorted(unreachable))
            msg = f"Unreachable node(s): {names}."
            raise GraphValidationError(msg)
