"""Graph builder for the sequential nano-agentgraph runtime."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from nano_agentgraph.errors import GraphValidationError
from nano_agentgraph.graph.compiled import CompiledStateGraph
from nano_agentgraph.graph.constants import END, START
from nano_agentgraph.graph.state import parse_reducers


class StateGraph:
    """Build a small LangGraph-style state graph.

    The runtime intentionally stays sequential for now, while supporting the
    core LangGraph-style building blocks for reducers, conditional routing,
    Command routing, checkpointing, interrupts, and streaming.
    """

    def __init__(self, state_schema: type[Any] | None = None) -> None:
        self.state_schema = state_schema
        self._nodes: dict[str, Callable[[dict[str, Any]], Any]] = {}
        self._edges: dict[str, list[str]] = {}
        self._conditional_edges: dict[
            str,
            tuple[Callable[[dict[str, Any]], Any], dict[Any, str] | None],
        ] = {}

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
        path: Callable[[dict[str, Any]], Any],
        path_map: dict[Any, str] | None = None,
    ) -> StateGraph:
        """Register conditional routing from a node."""

        if not isinstance(source, str):
            msg = "add_conditional_edges(source, path) expects a string source."
            raise TypeError(msg)
        if source in {START, END}:
            msg = "Conditional edges must start from a real node."
            raise GraphValidationError(msg)
        if not callable(path):
            msg = "Conditional edge path must be callable."
            raise TypeError(msg)
        if path_map is not None and not isinstance(path_map, dict):
            msg = "path_map must be a dictionary when provided."
            raise TypeError(msg)
        if source in self._conditional_edges:
            msg = f"Conditional edges for {source!r} already exist."
            raise GraphValidationError(msg)

        self._conditional_edges[source] = (
            path,
            dict(path_map) if path_map is not None else None,
        )
        return self

    def compile(
        self,
        checkpointer: Any | None = None,
        interrupt_before: Any | None = None,
        interrupt_after: Any | None = None,
        debug: bool = False,
    ) -> CompiledStateGraph:
        """Validate and compile the graph into an invokable runtime."""

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
            conditional_edges=dict(self._conditional_edges),
            reducers=parse_reducers(self.state_schema),
            checkpointer=checkpointer,
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
                    "parallel routing is not implemented yet."
                )
                raise GraphValidationError(msg)
            for target in targets:
                if target != END and target not in self._nodes:
                    msg = f"Edge target {target!r} is not a known node."
                    raise GraphValidationError(msg)

        for source, (_, path_map) in self._conditional_edges.items():
            if source not in self._nodes:
                msg = f"Conditional edge source {source!r} is not a known node."
                raise GraphValidationError(msg)
            if path_map is None:
                continue
            for target in path_map.values():
                if target == START:
                    msg = "START cannot be used as a conditional edge target."
                    raise GraphValidationError(msg)
                if target != END and target not in self._nodes:
                    msg = f"Conditional edge target {target!r} is not a known node."
                    raise GraphValidationError(msg)
