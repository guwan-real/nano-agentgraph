from nano_agentgraph.checkpoint.memory import InMemorySaver
from nano_agentgraph.graph import END, START, StateGraph


def node(state):
    return {"count": state["count"] + 1}


def main():
    graph = (
        StateGraph(dict)
        .add_node("node", node)
        .add_edge(START, "node")
        .add_edge("node", END)
        .compile(checkpointer=InMemorySaver())
    )
    config = {"configurable": {"thread_id": "demo"}}
    result = graph.invoke({"count": 0}, config=config)
    snapshot = graph.get_state(config)
    assert result == {"count": 1}
    assert snapshot.values == result
    return snapshot.values


if __name__ == "__main__":
    print(main())
