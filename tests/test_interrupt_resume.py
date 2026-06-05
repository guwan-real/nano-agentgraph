import pytest
from typing_extensions import TypedDict

from nano_agentgraph.checkpoint.memory import InMemorySaver
from nano_agentgraph.errors import GraphValidationError
from nano_agentgraph.graph import END, START, StateGraph
from nano_agentgraph.types import Command, interrupt


class ApprovalState(TypedDict):
    draft: str
    approved: bool


def test_interrupt_resume_approval_example():
    def approval(state: ApprovalState):
        approved = interrupt(
            {"question": "Approve draft?", "draft": state["draft"]},
        )
        return {"approved": bool(approved)}

    graph = (
        StateGraph(ApprovalState)
        .add_node("approval", approval)
        .add_edge(START, "approval")
        .add_edge("approval", END)
        .compile(checkpointer=InMemorySaver())
    )
    config = {"configurable": {"thread_id": "demo"}}

    first = graph.invoke({"draft": "hello", "approved": False}, config=config)
    assert first["__interrupt__"] == {
        "question": "Approve draft?",
        "draft": "hello",
    }

    second = graph.invoke(Command(resume=True), config=config)
    assert second == {"draft": "hello", "approved": True}
    assert graph.get_state(config).values == second


def test_interrupt_requires_checkpointer():
    def approval(state):
        interrupt({"question": "Approve?"})
        return {"approved": True}

    graph = (
        StateGraph(dict)
        .add_node("approval", approval)
        .add_edge(START, "approval")
        .add_edge("approval", END)
        .compile()
    )

    with pytest.raises(GraphValidationError, match="checkpointer"):
        graph.invoke({"approved": False})


def test_interrupt_requires_thread_id():
    def approval(state):
        interrupt({"question": "Approve?"})
        return {"approved": True}

    graph = (
        StateGraph(dict)
        .add_node("approval", approval)
        .add_edge(START, "approval")
        .add_edge("approval", END)
        .compile(checkpointer=InMemorySaver())
    )

    with pytest.raises(GraphValidationError, match="thread_id"):
        graph.invoke({"approved": False})


def test_interrupt_payload_must_be_json_serializable():
    def approval(state):
        interrupt({"bad": object()})
        return {}

    graph = (
        StateGraph(dict)
        .add_node("approval", approval)
        .add_edge(START, "approval")
        .add_edge("approval", END)
        .compile(checkpointer=InMemorySaver())
    )
    config = {"configurable": {"thread_id": "demo"}}

    with pytest.raises(GraphValidationError, match="JSON-serializable"):
        graph.invoke({}, config=config)
