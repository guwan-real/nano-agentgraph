# nano-agentgraph

A tiny, readable, LangGraph-style graph runtime for learning and hacking agent
orchestration.

```python
from nano_agentgraph.graph import StateGraph, START, END
from nano_agentgraph.types import Command, interrupt
```

This first milestone supports import-compatible paths and simple sequential
state graphs. It is not a production replacement for LangGraph.
