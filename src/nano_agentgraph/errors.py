"""Project-specific errors for nano-agentgraph."""


class GraphError(Exception):
    """Base class for graph construction and runtime errors."""


class GraphValidationError(GraphError):
    """Raised when a graph cannot be compiled safely."""


class InvalidUpdateError(GraphError):
    """Raised when a node returns an unsupported update value."""
