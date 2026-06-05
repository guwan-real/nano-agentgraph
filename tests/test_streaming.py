from operator import add
from typing import Annotated

import pytest
from typing_extensions import TypedDict

from nano_agentgraph.graph import END, START, StateGraph


def test_stream_values_yields_full_state_after_each_node():
    def inc(state):
        return {"x": state["x"] + 1}

    def double(state):
        return {"y": state["x"] * 2}

    graph = (
        StateGraph(dict)
        .add_node("inc", inc)
        .add_node("double", double)
        .add_edge(START, "inc")
        .add_edge("inc", "double")
        .add_edge("double", END)
        .compile()
    )

    assert list(graph.stream({"x": 1}, stream_mode="values")) == [
        {"type": "values", "ns": (), "data": {"x": 2}},
        {"type": "values", "ns": (), "data": {"x": 2, "y": 4}},
    ]


def test_stream_updates_yields_node_updates_after_reducers_apply():
    class State(TypedDict):
        log: Annotated[list[str], add]

    def write(state):
        return {"log": ["node"]}

    graph = (
        StateGraph(State)
        .add_node("write", write)
        .add_edge(START, "write")
        .add_edge("write", END)
        .compile()
    )

    assert list(graph.stream({"log": ["seed"]}, stream_mode="updates")) == [
        {"type": "updates", "ns": (), "data": {"write": {"log": ["seed", "node"]}}},
    ]


def test_stream_mode_list_uses_requested_order():
    def node(state):
        return {"x": 1}

    graph = (
        StateGraph(dict)
        .add_node("node", node)
        .add_edge(START, "node")
        .add_edge("node", END)
        .compile()
    )

    assert list(graph.stream({}, stream_mode=["updates", "values"])) == [
        {"type": "updates", "ns": (), "data": {"node": {"x": 1}}},
        {"type": "values", "ns": (), "data": {"x": 1}},
    ]


def test_unsupported_stream_modes_raise_clear_error():
    graph = (
        StateGraph(dict)
        .add_node("node", lambda state: {})
        .add_edge(START, "node")
        .add_edge("node", END)
        .compile()
    )

    with pytest.raises(NotImplementedError, match="messages"):
        list(graph.stream({}, stream_mode="messages"))
