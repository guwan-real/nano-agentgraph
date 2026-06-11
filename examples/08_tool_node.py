from operator import add
from typing import Annotated

from typing_extensions import TypedDict

from nano_agentgraph.graph import END, START, StateGraph
from nano_agentgraph.prebuilt import ToolNode, tools_condition


class State(TypedDict):
    messages: Annotated[list[dict], add]


def agent(state):
    return {
        "messages": [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"name": "search", "args": {"q": "cats"}}],
            },
        ],
    }


def search(q: str) -> str:
    return f"result for {q}"


def main():
    graph = (
        StateGraph(State)
        .add_node("agent", agent)
        .add_node("tools", ToolNode([search]))
        .add_edge(START, "agent")
        .add_conditional_edges("agent", tools_condition)
        .add_edge("tools", END)
        .compile()
    )
    result = graph.invoke({"messages": []})
    assert result["messages"][-1] == {
        "role": "tool",
        "name": "search",
        "content": "result for cats",
    }
    return result


if __name__ == "__main__":
    print(main())
