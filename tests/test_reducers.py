from dataclasses import dataclass
from operator import add
from typing import Annotated

from typing_extensions import TypedDict

from nano_agentgraph.graph import END, START, StateGraph


class ReducerState(TypedDict):
    foo: int
    bar: Annotated[list[str], add]


def test_annotated_reducer_appends_per_key_without_mutating_input():
    def append_bar(state):
        return {"bar": ["bye"]}

    def overwrite_foo(state):
        return {"foo": state["foo"] + 1}

    input_state = {"foo": 1, "bar": ["hi"]}
    graph = (
        StateGraph(ReducerState)
        .add_node("append_bar", append_bar)
        .add_node("overwrite_foo", overwrite_foo)
        .add_edge(START, "append_bar")
        .add_edge("append_bar", "overwrite_foo")
        .add_edge("overwrite_foo", END)
        .compile()
    )

    result = graph.invoke(input_state)

    assert input_state == {"foo": 1, "bar": ["hi"]}
    assert result == {"foo": 2, "bar": ["hi", "bye"]}


@dataclass
class DataclassState:
    items: Annotated[list[int], add]


def test_dataclass_schema_reducers_are_supported():
    def add_items(state):
        return {"items": [2, 3]}

    graph = (
        StateGraph(DataclassState)
        .add_node("add_items", add_items)
        .add_edge(START, "add_items")
        .add_edge("add_items", END)
        .compile()
    )

    assert graph.invoke({"items": [1]}) == {"items": [1, 2, 3]}


def test_missing_old_reducer_value_uses_update_directly():
    def initialize(state):
        return {"bar": ["first"]}

    graph = (
        StateGraph(ReducerState)
        .add_node("initialize", initialize)
        .add_edge(START, "initialize")
        .add_edge("initialize", END)
        .compile()
    )

    assert graph.invoke({"foo": 1}) == {"foo": 1, "bar": ["first"]}
