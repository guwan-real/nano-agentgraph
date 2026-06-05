import pytest

from nano_agentgraph.checkpoint.base import Checkpoint
from nano_agentgraph.checkpoint.memory import InMemorySaver
from nano_agentgraph.errors import GraphValidationError
from nano_agentgraph.graph import END, START, StateGraph


def test_memory_saver_is_thread_scoped_and_copies_values():
    saver = InMemorySaver()
    checkpoint = Checkpoint(
        thread_id="a",
        step=1,
        next_node=None,
        state={"items": ["original"]},
    )

    saver.put("a", checkpoint)
    checkpoint.state["items"].append("mutated")
    saver.put("b", Checkpoint("b", 1, None, {"items": ["other"]}))

    assert saver.get_latest("a").state == {"items": ["original"]}
    assert saver.get_latest("b").state == {"items": ["other"]}
    assert len(saver.list("a")) == 1


def test_graph_writes_checkpoints_and_get_state_returns_latest_snapshot():
    saver = InMemorySaver()

    def first(state):
        return {"x": 1}

    def second(state):
        return {"y": state["x"] + 1}

    graph = (
        StateGraph(dict)
        .add_node("first", first)
        .add_node("second", second)
        .add_edge(START, "first")
        .add_edge("first", "second")
        .add_edge("second", END)
        .compile(checkpointer=saver)
    )
    config = {"configurable": {"thread_id": "demo"}}

    assert graph.invoke({}, config=config) == {"x": 1, "y": 2}

    checkpoints = saver.list("demo")
    assert [checkpoint.next_node for checkpoint in checkpoints] == ["second", None]
    snapshot = graph.get_state(config)
    assert snapshot.values == {"x": 1, "y": 2}
    assert snapshot.next == ()
    assert snapshot.metadata["step"] == 2


def test_update_state_applies_values_to_latest_checkpoint():
    saver = InMemorySaver()
    graph = (
        StateGraph(dict)
        .add_node("node", lambda state: {"x": 1})
        .add_edge(START, "node")
        .add_edge("node", END)
        .compile(checkpointer=saver)
    )
    config = {"configurable": {"thread_id": "demo"}}

    graph.invoke({}, config=config)
    snapshot = graph.update_state(config, {"x": 3, "y": 4}, as_node="manual")

    assert snapshot.values == {"x": 3, "y": 4}
    assert snapshot.metadata["as_node"] == "manual"
    assert graph.get_state(config).values == {"x": 3, "y": 4}


def test_checkpointer_requires_thread_id_config():
    graph = (
        StateGraph(dict)
        .add_node("node", lambda state: {})
        .add_edge(START, "node")
        .add_edge("node", END)
        .compile(checkpointer=InMemorySaver())
    )

    with pytest.raises(GraphValidationError, match="thread_id"):
        graph.invoke({})
