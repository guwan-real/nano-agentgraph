from nano_agentgraph.graph import END, START, StateGraph
from nano_agentgraph.types import Command


def planner(state):
    return Command(update={"planned": True}, goto="worker")


def worker(state):
    return {"worked": state["planned"]}


def main():
    graph = (
        StateGraph(dict)
        .add_node("planner", planner)
        .add_node("worker", worker)
        .add_edge(START, "planner")
        .add_edge("worker", END)
        .compile()
    )
    result = graph.invoke({})
    assert result == {"planned": True, "worked": True}
    return result


if __name__ == "__main__":
    print(main())
