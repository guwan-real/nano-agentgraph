import pytest

from nano_agentgraph.checkpoint.memory import InMemorySaver
from nano_agentgraph.errors import (
    CheckpointError,
    GraphRecursionError,
    GraphValidationError,
    InterruptError,
)
from nano_agentgraph.graph import END, START, StateGraph
from nano_agentgraph.types import Command


def test_recursion_limit_stops_cycles():
    graph = (
        StateGraph(dict)
        .add_node("loop", lambda state: {"count": state["count"] + 1})
        .add_edge(START, "loop")
        .add_edge("loop", "loop")
        .compile()
    )

    with pytest.raises(GraphRecursionError, match="recursion_limit=3"):
        graph.invoke({"count": 0}, config={"recursion_limit": 3})


def test_invalid_recursion_limit_is_rejected():
    graph = (
        StateGraph(dict)
        .add_node("node", lambda state: {})
        .add_edge(START, "node")
        .add_edge("node", END)
        .compile()
    )

    with pytest.raises(GraphValidationError, match="recursion_limit"):
        graph.invoke({}, config={"recursion_limit": 0})


def test_static_and_conditional_routes_cannot_be_mixed():
    graph = (
        StateGraph(dict)
        .add_node("node", lambda state: {})
        .add_edge(START, "node")
        .add_edge("node", END)
        .add_conditional_edges("node", lambda state: END)
    )

    with pytest.raises(GraphValidationError, match="both static and conditional"):
        graph.compile()


def test_resume_without_interrupted_checkpoint_raises_interrupt_error():
    graph = (
        StateGraph(dict)
        .add_node("node", lambda state: {})
        .add_edge(START, "node")
        .add_edge("node", END)
        .compile(checkpointer=InMemorySaver())
    )

    with pytest.raises(InterruptError, match="no interrupted checkpoint"):
        graph.invoke(Command(resume=True), config={"configurable": {"thread_id": "t"}})


def test_get_state_without_checkpointer_raises_checkpoint_error():
    graph = (
        StateGraph(dict)
        .add_node("node", lambda state: {})
        .add_edge(START, "node")
        .add_edge("node", END)
        .compile()
    )

    with pytest.raises(CheckpointError, match="without a checkpointer"):
        graph.get_state({"configurable": {"thread_id": "t"}})


def test_stream_executes_incrementally():
    seen: list[str] = []

    def first(state):
        seen.append("first")
        return {"x": 1}

    def second(state):
        seen.append("second")
        return {"y": 2}

    graph = (
        StateGraph(dict)
        .add_node("first", first)
        .add_node("second", second)
        .add_edge(START, "first")
        .add_edge("first", "second")
        .add_edge("second", END)
        .compile()
    )

    stream = graph.stream({}, stream_mode="values")
    assert seen == []
    assert next(stream) == {"type": "values", "ns": (), "data": {"x": 1}}
    assert seen == ["first"]
    assert next(stream) == {"type": "values", "ns": (), "data": {"x": 1, "y": 2}}
    assert seen == ["first", "second"]
