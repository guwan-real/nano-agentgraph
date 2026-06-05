from typing_extensions import TypedDict

from nano_agentgraph.checkpoint.memory import InMemorySaver
from nano_agentgraph.graph import END, START, StateGraph
from nano_agentgraph.types import Command, interrupt


class State(TypedDict):
    draft: str
    approved: bool


def approval(state: State):
    approved = interrupt({"question": "Approve draft?", "draft": state["draft"]})
    return {"approved": bool(approved)}


def main():
    graph = (
        StateGraph(State)
        .add_node("approval", approval)
        .add_edge(START, "approval")
        .add_edge("approval", END)
        .compile(checkpointer=InMemorySaver())
    )
    config = {"configurable": {"thread_id": "demo"}}
    first = graph.invoke({"draft": "hello", "approved": False}, config=config)
    assert "__interrupt__" in first
    second = graph.invoke(Command(resume=True), config=config)
    assert second == {"draft": "hello", "approved": True}
    return second


if __name__ == "__main__":
    print(main())
