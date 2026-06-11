"""Project-specific errors for nano-agentgraph."""


class GraphError(Exception):
    """Base class for graph construction and runtime errors."""


class GraphValidationError(GraphError):
    """Raised when a graph cannot be compiled safely."""


class GraphRecursionError(GraphError):
    """Raised when graph execution exceeds its recursion limit."""


class CheckpointError(GraphValidationError):
    """Raised when checkpoint configuration or state is invalid."""


class InterruptError(GraphValidationError):
    """Raised when interrupt or resume usage is invalid."""


class InvalidUpdateError(GraphError):
    """Raised when a node returns an unsupported update value."""
