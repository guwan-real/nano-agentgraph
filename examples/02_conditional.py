from nano_agentgraph.graph import END, START, StateGraph


def planner(state):
    return {"planned": True}


def worker(state):
    return {"worked": True}


def route(state):
    return "worker" if state["ready"] else END


def main():
    graph = (
        StateGraph(dict)
        .add_node("planner", planner)
        .add_node("worker", worker)
        .add_edge(START, "planner")
        .add_conditional_edges("planner", route)
        .add_edge("worker", END)
        .compile()
    )
    result = graph.invoke({"ready": True})
    assert result == {"ready": True, "planned": True, "worked": True}
    return result


if __name__ == "__main__":
    print(main())
