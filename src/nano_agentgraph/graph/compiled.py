"""Compiled sequential graph runtime."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from nano_agentgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint
from nano_agentgraph.errors import (
    CheckpointError,
    GraphRecursionError,
    GraphValidationError,
    InterruptError,
    InvalidUpdateError,
)
from nano_agentgraph.graph.constants import END, START
from nano_agentgraph.graph.state import StateSnapshot
from nano_agentgraph.types import (
    _NO_RESUME,
    Command,
    _current_interrupt_context,
    _GraphInterrupt,
    _InterruptContext,
)

DEFAULT_RECURSION_LIMIT = 25


@dataclass(slots=True)
class _RunPosition:
    state: dict[str, Any]
    current: str
    thread_id: str | None
    step: int
    resume: Any = _NO_RESUME


@dataclass(slots=True)
class _StepResult:
    node: str
    update: dict[str, Any]
    state: dict[str, Any]


class CompiledStateGraph:
    """A compiled graph that executes one node at a time."""

    def __init__(
        self,
        nodes: dict[str, Callable[[dict[str, Any]], Any]],
        edges: dict[str, list[str]],
        conditional_edges: dict[
            str,
            tuple[Callable[[dict[str, Any]], Any], dict[Any, str] | None],
        ],
        reducers: dict[str, Callable[[Any, Any], Any]],
        checkpointer: BaseCheckpointSaver | None = None,
    ) -> None:
        self._nodes = nodes
        self._edges = edges
        self._conditional_edges = conditional_edges
        self._reducers = reducers
        self._checkpointer = checkpointer

    def invoke(
        self,
        input: dict[str, Any] | Command,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run the graph to END and return the final state."""

        return self._execute(input, config)

    def stream(
        self,
        input: dict[str, Any] | Command,
        config: dict[str, Any] | None = None,
        *,
        stream_mode: str | list[str] = "values",
        version: str = "v2",
    ) -> Iterator[dict[str, Any]]:
        """Stream v2-style updates or values events."""

        if version != "v2":
            msg = "Only stream version 'v2' is supported."
            raise NotImplementedError(msg)
        modes = self._normalize_stream_modes(stream_mode)
        position = self._start_position(input, config)
        limit = self._recursion_limit(config)
        executed = 0

        while position.current != END:
            if limit is not None and executed >= limit:
                self._raise_recursion_error(limit)
            try:
                step = self._run_one(position)
            except _GraphInterrupt as interrupt:
                self._handle_interrupt(interrupt, position)
                return
            executed += 1
            for mode in modes:
                if mode == "updates":
                    data = {step.node: deepcopy(step.update)}
                else:
                    data = deepcopy(step.state)
                yield {"type": mode, "ns": (), "data": data}

    def get_state(self, config: dict[str, Any]) -> StateSnapshot:
        """Return the latest checkpointed state for a thread."""

        thread_id = self._require_thread_id(config)
        latest = self._require_checkpointer().get_latest(thread_id)
        if latest is None:
            return StateSnapshot(values={}, config=config)
        return self._snapshot_from_checkpoint(latest, config)

    def update_state(
        self,
        config: dict[str, Any],
        values: dict[str, Any],
        as_node: str | None = None,
    ) -> StateSnapshot:
        """Apply a manual update to the latest checkpointed state."""

        if not isinstance(values, dict):
            msg = "update_state(values) expects a dictionary."
            raise TypeError(msg)
        thread_id = self._require_thread_id(config)
        checkpointer = self._require_checkpointer()
        latest = checkpointer.get_latest(thread_id)
        state = {} if latest is None else latest.state
        applied = self._apply_update(state, values)
        next_node = None if latest is None else latest.next_node
        step = 1 if latest is None else latest.step + 1
        checkpoint = Checkpoint(
            thread_id=thread_id,
            step=step,
            next_node=next_node,
            state=state,
            interrupted=False if latest is None else latest.interrupted,
            interrupt_payload=None if latest is None else latest.interrupt_payload,
        )
        checkpointer.put(thread_id, checkpoint)
        metadata = {"source": "update_state", "as_node": as_node, "update": applied}
        return self._snapshot_from_checkpoint(checkpoint, config, metadata=metadata)

    def _execute(
        self,
        input: dict[str, Any] | Command,
        config: dict[str, Any] | None,
    ) -> dict[str, Any]:
        position = self._start_position(input, config)
        limit = self._recursion_limit(config)
        executed = 0

        while position.current != END:
            if limit is not None and executed >= limit:
                self._raise_recursion_error(limit)
            try:
                self._run_one(position)
            except _GraphInterrupt as interrupt:
                return self._handle_interrupt(interrupt, position)
            executed += 1

        return position.state

    def _run_one(self, position: _RunPosition) -> _StepResult:
        node = position.current
        raw_update = self._call_node(node, position.state, position.resume)
        position.resume = _NO_RESUME
        command = raw_update if isinstance(raw_update, Command) else None
        update = self._coerce_update(node, raw_update)
        applied_update = self._apply_update(position.state, update)
        next_node = self._select_next(node, position.state, command)
        position.step += 1
        self._put_checkpoint(
            position.thread_id,
            position.step,
            next_node,
            position.state,
        )
        position.current = next_node
        return _StepResult(node=node, update=applied_update, state=position.state)

    def _start_position(
        self,
        input: dict[str, Any] | Command,
        config: dict[str, Any] | None,
    ) -> _RunPosition:
        if isinstance(input, Command):
            if input.resume is None:
                msg = "Only Command(resume=...) is supported as graph input."
                raise InterruptError(msg)
            thread_id = self._require_thread_id(config)
            latest = self._require_checkpointer().get_latest(thread_id)
            if latest is None or not latest.interrupted or latest.next_node is None:
                msg = "Cannot resume because no interrupted checkpoint exists."
                raise InterruptError(msg)
            return _RunPosition(
                state=latest.state,
                current=latest.next_node,
                thread_id=thread_id,
                step=latest.step,
                resume=input.resume,
            )

        if not isinstance(input, dict):
            msg = "invoke(input) expects a state dictionary or Command(resume=...)."
            raise TypeError(msg)

        thread_id = self._thread_id(config)
        if self._checkpointer is not None and thread_id is None:
            msg = "A checkpointer requires config['configurable']['thread_id']."
            raise CheckpointError(msg)
        latest = (
            self._checkpointer.get_latest(thread_id)
            if self._checkpointer is not None and thread_id is not None
            else None
        )
        return _RunPosition(
            state=deepcopy(input),
            current=self._next_static(START),
            thread_id=thread_id,
            step=0 if latest is None else latest.step,
        )

    def _call_node(self, node: str, state: dict[str, Any], resume: Any) -> Any:
        context = _InterruptContext(resume=resume)
        token = _current_interrupt_context.set(context)
        try:
            return self._nodes[node](deepcopy(state))
        finally:
            _current_interrupt_context.reset(token)

    def _coerce_update(self, node: str, value: Any) -> dict[str, Any]:
        update = value.update if isinstance(value, Command) else value
        if update is None:
            return {}
        if not isinstance(update, dict):
            msg = (
                f"Node {node!r} returned {type(update).__name__}; "
                "nodes must return a dict update or Command(update=...)."
            )
            raise InvalidUpdateError(msg)
        return update

    def _apply_update(
        self,
        state: dict[str, Any],
        update: dict[str, Any],
    ) -> dict[str, Any]:
        applied: dict[str, Any] = {}
        for key, value in update.items():
            if key in self._reducers and key in state:
                new_value = self._reducers[key](state[key], value)
            else:
                new_value = value
            state[key] = new_value
            applied[key] = new_value
        return applied

    def _select_next(
        self,
        source: str,
        state: dict[str, Any],
        command: Command | None,
    ) -> str:
        if command is not None and command.goto is not None:
            return self._resolve_target(command.goto)
        if source in self._conditional_edges:
            path, path_map = self._conditional_edges[source]
            route = path(deepcopy(state))
            return self._resolve_conditional_target(route, path_map)
        return self._next_static(source)

    def _resolve_conditional_target(
        self,
        route: Any,
        path_map: dict[Any, str] | None,
    ) -> str:
        if isinstance(route, list):
            msg = "parallel routing is not implemented yet."
            raise NotImplementedError(msg)
        if path_map is not None:
            if route not in path_map:
                msg = f"Conditional route {route!r} is not present in path_map."
                raise GraphValidationError(msg)
            return self._resolve_target(path_map[route])
        return self._resolve_target(route)

    def _resolve_target(self, target: Any) -> str:
        if isinstance(target, list):
            msg = "parallel routing is not implemented yet."
            raise NotImplementedError(msg)
        if not isinstance(target, str):
            msg = f"Route target must be a node name or END, got {target!r}."
            raise GraphValidationError(msg)
        if target != END and target not in self._nodes:
            msg = f"Route target {target!r} is not a known node."
            raise GraphValidationError(msg)
        return target

    def _next_static(self, source: str) -> str:
        targets = self._edges.get(source)
        if not targets:
            msg = (
                f"Node {source!r} has no route. Add a static edge, "
                "conditional edge, or return Command(goto=...)."
            )
            raise GraphValidationError(msg)
        return targets[0]

    def _handle_interrupt(
        self,
        interrupt: _GraphInterrupt,
        position: _RunPosition,
    ) -> dict[str, Any]:
        if self._checkpointer is None:
            msg = "interrupt() requires a graph compiled with a checkpointer."
            raise InterruptError(msg)
        if position.thread_id is None:
            msg = "interrupt() requires config['configurable']['thread_id']."
            raise InterruptError(msg)
        self._checkpointer.put(
            position.thread_id,
            Checkpoint(
                thread_id=position.thread_id,
                step=position.step,
                next_node=position.current,
                state=position.state,
                interrupted=True,
                interrupt_payload=interrupt.value,
            ),
        )
        return {**deepcopy(position.state), "__interrupt__": interrupt.value}

    def _put_checkpoint(
        self,
        thread_id: str | None,
        step: int,
        next_node: str,
        state: dict[str, Any],
    ) -> None:
        if self._checkpointer is None or thread_id is None:
            return
        self._checkpointer.put(
            thread_id,
            Checkpoint(
                thread_id=thread_id,
                step=step,
                next_node=None if next_node == END else next_node,
                state=state,
            ),
        )

    def _thread_id(self, config: dict[str, Any] | None) -> str | None:
        if config is None:
            return None
        configurable = config.get("configurable", {})
        if not isinstance(configurable, dict):
            msg = "config['configurable'] must be a dictionary."
            raise CheckpointError(msg)
        thread_id = configurable.get("thread_id")
        if thread_id is None:
            return None
        if not isinstance(thread_id, str):
            msg = "config['configurable']['thread_id'] must be a string."
            raise CheckpointError(msg)
        return thread_id

    def _require_thread_id(self, config: dict[str, Any] | None) -> str:
        thread_id = self._thread_id(config)
        if thread_id is None:
            msg = "Expected config['configurable']['thread_id']."
            raise CheckpointError(msg)
        return thread_id

    def _require_checkpointer(self) -> BaseCheckpointSaver:
        if self._checkpointer is None:
            msg = "This graph was compiled without a checkpointer."
            raise CheckpointError(msg)
        return self._checkpointer

    def _snapshot_from_checkpoint(
        self,
        checkpoint: Checkpoint,
        config: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> StateSnapshot:
        next_nodes = () if checkpoint.next_node is None else (checkpoint.next_node,)
        snapshot_metadata = {
            "step": checkpoint.step,
            "interrupted": checkpoint.interrupted,
            "interrupt_payload": checkpoint.interrupt_payload,
        }
        if metadata is not None:
            snapshot_metadata.update(metadata)
        return StateSnapshot(
            values=deepcopy(checkpoint.state),
            next=next_nodes,
            config=deepcopy(config),
            metadata=snapshot_metadata,
        )

    def _normalize_stream_modes(self, stream_mode: str | list[str]) -> list[str]:
        if isinstance(stream_mode, str):
            modes = [stream_mode]
        else:
            modes = list(stream_mode)
        supported = {"updates", "values"}
        unsupported = [mode for mode in modes if mode not in supported]
        if unsupported:
            names = ", ".join(repr(mode) for mode in unsupported)
            msg = f"Unsupported stream mode(s): {names}."
            raise NotImplementedError(msg)
        return modes

    def _recursion_limit(self, config: dict[str, Any] | None) -> int | None:
        if config is None:
            return DEFAULT_RECURSION_LIMIT
        raw_limit = config.get("recursion_limit", DEFAULT_RECURSION_LIMIT)
        if raw_limit is None:
            return None
        if not isinstance(raw_limit, int) or raw_limit < 1:
            msg = "config['recursion_limit'] must be a positive integer or None."
            raise GraphValidationError(msg)
        return raw_limit

    def _raise_recursion_error(self, limit: int) -> None:
        msg = (
            f"Graph execution exceeded recursion_limit={limit}. "
            "Pass a larger config['recursion_limit'] if this loop is intentional."
        )
        raise GraphRecursionError(msg)
