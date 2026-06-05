import pytest

from nano_agentgraph.graph import END, START, StateGraph


def test_conditional_edges_route_to_node_or_end():
    def planner(state):
        return {"planned": True}

    def worker(state):
        return {"worked": True}

    def route(state):
        return "worker" if state["ready"] else END

    graph = (
        StateGraph(dict)
        .add_node("planner", planner)
        .add_node("worker", worker)
        .add_edge(START, "planner")
        .add_conditional_edges("planner", route)
        .add_edge("worker", END)
        .compile()
    )

    assert graph.invoke({"ready": True}) == {
        "ready": True,
        "planned": True,
        "worked": True,
    }
    assert graph.invoke({"ready": False}) == {"ready": False, "planned": True}


def test_conditional_edges_support_path_map():
    def planner(state):
        return {"planned": True}

    def worker(state):
        return {"worked": True}

    def route(state):
        return "continue" if state["ready"] else "stop"

    graph = (
        StateGraph(dict)
        .add_node("planner", planner)
        .add_node("worker", worker)
        .add_edge(START, "planner")
        .add_conditional_edges("planner", route, {"continue": "worker", "stop": END})
        .add_edge("worker", END)
        .compile()
    )

    assert graph.invoke({"ready": True})["worked"] is True
    assert graph.invoke({"ready": False}) == {"ready": False, "planned": True}


def test_parallel_conditional_route_is_not_implemented():
    def planner(state):
        return {}

    def route(state):
        return ["one", "two"]

    graph = (
        StateGraph(dict)
        .add_node("planner", planner)
        .add_node("one", lambda state: {})
        .add_node("two", lambda state: {})
        .add_edge(START, "planner")
        .add_conditional_edges("planner", route)
        .add_edge("one", END)
        .add_edge("two", END)
        .compile()
    )

    with pytest.raises(NotImplementedError, match="parallel routing"):
        graph.invoke({})
