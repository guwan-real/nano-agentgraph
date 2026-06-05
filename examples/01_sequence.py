from typing_extensions import TypedDict

from nano_agentgraph.graph import END, START, StateGraph


class State(TypedDict):
    topic: str
    joke: str


def refine_topic(state: State):
    return {"topic": state["topic"] + " and cats"}


def generate_joke(state: State):
    return {"joke": f"This is a joke about {state['topic']}"}


def main():
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
    return result


if __name__ == "__main__":
    print(main())
