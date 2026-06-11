from operator import add
from typing import Annotated

import pytest
from typing_extensions import TypedDict

from nano_agentgraph.errors import GraphValidationError
from nano_agentgraph.graph import END, START, StateGraph
from nano_agentgraph.prebuilt import ToolNode, tools_condition


class State(TypedDict):
    messages: Annotated[list[dict], add]


def test_tool_node_import_and_execution():
    def search(q: str) -> str:
        return f"result for {q}"

    node = ToolNode([search])

    result = node(
        {
            "messages": [
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {"id": "call-1", "name": "search", "args": {"q": "cats"}},
                    ],
                },
            ],
        },
    )

    assert result == {
        "messages": [
            {
                "role": "tool",
                "name": "search",
                "content": "result for cats",
                "tool_call_id": "call-1",
            },
        ],
    }


def test_tools_condition_routes_graph_to_tools_node():
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
        return q.upper()

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
        "content": "CATS",
    }


def test_tools_condition_ends_without_tool_calls():
    state = {"messages": [{"role": "assistant", "content": "done"}]}

    assert tools_condition(state) == END


def test_tool_node_rejects_unknown_tool():
    node = ToolNode({"known": lambda: "ok"})

    with pytest.raises(GraphValidationError, match="Unknown tool"):
        node({"messages": [{"tool_calls": [{"name": "missing", "args": {}}]}]})
