from nano_agentgraph.graph import END, START, StateGraph


def inc(state):
    return {"count": state["count"] + 1}


def label(state):
    return {"label": f"count={state['count']}"}


def main():
    graph = (
        StateGraph(dict)
        .add_node("inc", inc)
        .add_node("label", label)
        .add_edge(START, "inc")
        .add_edge("inc", "label")
        .add_edge("label", END)
        .compile()
    )
    events = list(graph.stream({"count": 0}, stream_mode=["updates", "values"]))
    assert events == [
        {"type": "updates", "ns": (), "data": {"inc": {"count": 1}}},
        {"type": "values", "ns": (), "data": {"count": 1}},
        {"type": "updates", "ns": (), "data": {"label": {"label": "count=1"}}},
        {"type": "values", "ns": (), "data": {"count": 1, "label": "count=1"}},
    ]
    return events


if __name__ == "__main__":
    for event in main():
        print(event)
