import pytest
from typing_extensions import TypedDict

from nano_agentgraph.errors import GraphValidationError, InvalidUpdateError
from nano_agentgraph.graph import END, START, StateGraph


class State(TypedDict):
    topic: str
    joke: str


def refine_topic(state: State):
    return {"topic": state["topic"] + " and cats"}


def generate_joke(state: State):
    return {"joke": f"This is a joke about {state['topic']}"}


def test_docs_style_graph():
    graph = (
        StateGraph(State)
        .add_node(refine_topic)
        .add_node(generate_joke)
        .add_edge(START, "refine_topic")
        .add_edge("refine_topic", "generate_joke")
        .add_edge("generate_joke", END)
        .compile()
    )

    result = graph.invoke({"topic": "ice cream"})

    assert result == {
        "topic": "ice cream and cats",
        "joke": "This is a joke about ice cream and cats",
    }


def test_explicit_node_names_and_partial_updates_do_not_mutate_input():
    def planner(state):
        return {"task": state["task"] + ": planned"}

    def worker(state):
        return {"done": True}

    input_state = {"task": "demo"}
    graph = StateGraph(dict)
    graph.add_node("planner", planner)
    graph.add_node("worker", worker)
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "worker")
    graph.add_edge("worker", END)

    result = graph.compile().invoke(input_state)

    assert input_state == {"task": "demo"}
    assert result == {"task": "demo: planned", "done": True}


def test_set_entry_and_finish_point_wrappers():
    def only_node(state):
        return {"count": state["count"] + 1}

    graph = (
        StateGraph(dict)
        .add_node("only", only_node)
        .set_entry_point("only")
        .set_finish_point("only")
        .compile()
    )

    assert graph.invoke({"count": 1}) == {"count": 2}


def test_compile_rejects_missing_start_edge():
    graph = StateGraph(dict).add_node("node", lambda state: {})

    with pytest.raises(GraphValidationError, match="START"):
        graph.compile()


def test_compile_rejects_unknown_edge_target():
    graph = StateGraph(dict).add_node("node", lambda state: {})
    graph.add_edge(START, "missing")

    with pytest.raises(GraphValidationError, match="missing"):
        graph.compile()


def test_compile_rejects_parallel_static_edges_for_m1():
    graph = StateGraph(dict)
    graph.add_node("one", lambda state: {})
    graph.add_node("two", lambda state: {})
    graph.add_edge(START, "one")
    graph.add_edge(START, "two")
    graph.add_edge("one", END)
    graph.add_edge("two", END)

    with pytest.raises(GraphValidationError, match="multiple outgoing edges"):
        graph.compile()


def test_node_must_return_dict_update():
    def bad_node(state):
        return "nope"

    graph = (
        StateGraph(dict)
        .add_node("bad", bad_node)
        .add_edge(START, "bad")
        .add_edge("bad", END)
        .compile()
    )

    with pytest.raises(InvalidUpdateError, match="must return a dict"):
        graph.invoke({})
