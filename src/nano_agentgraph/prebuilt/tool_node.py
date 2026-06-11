"""Plain-dict tool calling helpers."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from nano_agentgraph.errors import GraphValidationError
from nano_agentgraph.graph import END


class ToolNode:
    """Execute tool calls from the last assistant message in state."""

    def __init__(
        self,
        tools: Iterable[Callable[..., Any]] | dict[str, Callable[..., Any]],
    ) -> None:
        if isinstance(tools, dict):
            self._tools = dict(tools)
        else:
            self._tools = {self._tool_name(tool): tool for tool in tools}
        if not self._tools:
            msg = "ToolNode requires at least one tool."
            raise GraphValidationError(msg)

    def __call__(self, state: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        messages = state.get("messages", [])
        if not isinstance(messages, list) or not messages:
            msg = "ToolNode expects state['messages'] to contain messages."
            raise GraphValidationError(msg)
        last = messages[-1]
        if not isinstance(last, dict):
            msg = "ToolNode messages must be dictionaries."
            raise GraphValidationError(msg)

        tool_calls = last.get("tool_calls", [])
        if not isinstance(tool_calls, list):
            msg = "assistant message 'tool_calls' must be a list."
            raise GraphValidationError(msg)

        results = [self._run_call(call) for call in tool_calls]
        return {"messages": results}

    def _run_call(self, call: Any) -> dict[str, Any]:
        if not isinstance(call, dict):
            msg = "tool calls must be dictionaries."
            raise GraphValidationError(msg)
        name = call.get("name")
        args = call.get("args", {})
        if not isinstance(name, str) or name not in self._tools:
            msg = f"Unknown tool call {name!r}."
            raise GraphValidationError(msg)
        if not isinstance(args, dict):
            msg = f"Tool call {name!r} args must be a dictionary."
            raise GraphValidationError(msg)

        result = self._tools[name](**args)
        message = {"role": "tool", "name": name, "content": str(result)}
        if "id" in call:
            message["tool_call_id"] = call["id"]
        return message

    @staticmethod
    def _tool_name(tool: Callable[..., Any]) -> str:
        name = getattr(tool, "__name__", None)
        if not name:
            msg = "Tool callables need a __name__; pass a dict for explicit names."
            raise GraphValidationError(msg)
        return name


def tools_condition(state: dict[str, Any]) -> str:
    """Route to a node named 'tools' when the last assistant message has calls."""

    messages = state.get("messages", [])
    if not isinstance(messages, list) or not messages:
        return END
    last = messages[-1]
    if not isinstance(last, dict):
        return END
    tool_calls = last.get("tool_calls")
    return "tools" if isinstance(tool_calls, list) and len(tool_calls) > 0 else END
