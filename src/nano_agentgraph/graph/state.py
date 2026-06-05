"""State helpers for compiled graph execution."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Annotated, Any, get_args, get_origin, get_type_hints


@dataclass(slots=True)
class StateSnapshot:
    """A lightweight saved-state snapshot."""

    values: dict[str, Any]
    next: tuple[str, ...] = ()
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


def parse_reducers(
    state_schema: type[Any] | None,
) -> dict[str, Callable[[Any, Any], Any]]:
    """Extract per-key reducer callables from typing.Annotated metadata."""

    if state_schema is None or state_schema is dict:
        return {}

    try:
        hints = get_type_hints(state_schema, include_extras=True)
    except (NameError, TypeError, AttributeError):
        hints = getattr(state_schema, "__annotations__", {})

    reducers: dict[str, Callable[[Any, Any], Any]] = {}
    for key, hint in hints.items():
        if get_origin(hint) is not Annotated:
            continue
        for metadata in get_args(hint)[1:]:
            if callable(metadata):
                reducers[key] = metadata
                break
    return reducers
