from operator import add
from typing import Annotated

from typing_extensions import TypedDict

from nano_agentgraph.graph import END, START, StateGraph


class State(TypedDict):
    log: Annotated[list[str], add]


def first(state):
    return {"log": ["first"]}


def second(state):
    return {"log": ["second"]}


def main():
    graph = (
        StateGraph(State)
        .add_node("first", first)
        .add_node("second", second)
        .add_edge(START, "first")
        .add_edge("first", "second")
        .add_edge("second", END)
        .compile()
    )
    result = graph.invoke({"log": ["start"]})
    assert result == {"log": ["start", "first", "second"]}
    return result


if __name__ == "__main__":
    print(main())
