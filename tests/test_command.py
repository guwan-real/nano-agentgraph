import pytest

from nano_agentgraph.errors import GraphValidationError, InvalidUpdateError
from nano_agentgraph.graph import END, START, StateGraph
from nano_agentgraph.types import Command


def test_command_update_and_goto_routes_dynamically():
    def planner(state):
        return Command(update={"planned": True}, goto="worker")

    def worker(state):
        return {"worked": state["planned"]}

    graph = (
        StateGraph(dict)
        .add_node("planner", planner)
        .add_node("worker", worker)
        .add_edge(START, "planner")
        .add_edge("worker", END)
        .compile()
    )

    assert graph.invoke({}) == {"planned": True, "worked": True}


def test_command_goto_takes_priority_over_static_edge():
    def planner(state):
        return Command(update={"path": "dynamic"}, goto="dynamic")

    graph = (
        StateGraph(dict)
        .add_node("planner", planner)
        .add_node("static", lambda state: {"path": "static"})
        .add_node("dynamic", lambda state: {"done": True})
        .add_edge(START, "planner")
        .add_edge("planner", "static")
        .add_edge("static", END)
        .add_edge("dynamic", END)
        .compile()
    )

    assert graph.invoke({}) == {"path": "dynamic", "done": True}


def test_command_update_must_be_dict_when_present():
    def bad_node(state):
        return Command(update="bad", goto=END)

    graph = (
        StateGraph(dict)
        .add_node("bad", bad_node)
        .add_edge(START, "bad")
        .compile()
    )

    with pytest.raises(InvalidUpdateError, match="dict update"):
        graph.invoke({})


def test_command_goto_unknown_node_raises_clear_error():
    def bad_node(state):
        return Command(goto="missing")

    graph = (
        StateGraph(dict)
        .add_node("bad", bad_node)
        .add_edge(START, "bad")
        .compile()
    )

    with pytest.raises(GraphValidationError, match="missing"):
        graph.invoke({})
