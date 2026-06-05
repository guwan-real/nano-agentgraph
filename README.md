# nano-agentgraph

**Language:** [English](#english) | [中文](#zh-cn)

<a id="english"></a>

## English

A tiny, readable, LangGraph-style graph runtime for learning and hacking agent
orchestration.

```python
from nano_agentgraph.graph import StateGraph, START, END
from nano_agentgraph.types import Command, interrupt
```

nano-agentgraph is designed for API familiarity, not full LangGraph
compatibility. A user who knows basic LangGraph examples should be able to keep
the same code shape and change the import prefix to `nano_agentgraph` for the
supported subset.

> This project is not a production replacement for LangGraph.

### Install

```bash
pip install -e ".[dev]"
```

### 30-second example

```python
from typing_extensions import TypedDict
from nano_agentgraph.graph import StateGraph, START, END


class State(TypedDict):
    topic: str
    joke: str


def refine_topic(state: State):
    return {"topic": state["topic"] + " and cats"}


def generate_joke(state: State):
    return {"joke": f"This is a joke about {state['topic']}"}


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
```

### Import mapping

| LangGraph | nano-agentgraph |
|---|---|
| `from langgraph.graph import StateGraph, START, END` | `from nano_agentgraph.graph import StateGraph, START, END` |
| `from langgraph.types import Command, interrupt` | `from nano_agentgraph.types import Command, interrupt` |
| `from langgraph.checkpoint.memory import InMemorySaver` | `from nano_agentgraph.checkpoint.memory import InMemorySaver` |

Top-level convenience imports also work:

```python
from nano_agentgraph import StateGraph, START, END, Command, interrupt, InMemorySaver
```

### Current supported subset

| Feature | Status |
|---|---|
| `StateGraph(state_schema)` | Supported |
| `START` and `END` | Supported |
| `add_node(name, fn)` | Supported |
| `add_node(fn)` name inference | Supported |
| `add_edge(source, target)` | Supported for one sequential path |
| `set_entry_point(name)` | Supported |
| `set_finish_point(name)` | Supported |
| `compile()` | Supported for sequential graphs |
| `CompiledStateGraph.invoke(input)` | Supported |
| Partial dict updates | Supported with overwrite semantics |
| Input state mutation protection | Supported |
| Reducers from `typing.Annotated` | Planned |
| Conditional edges | Planned |
| `Command(update=..., goto=...)` routing | Planned |
| In-memory checkpointing | Planned |
| Interrupt and resume | Planned |
| Streaming | Planned |

Unsupported advanced features raise clear `NotImplementedError` or
project-specific validation errors.

### Non-goals for the first release

- Full LangGraph API compatibility
- Real Pregel parallel supersteps
- Subgraphs and parent graph navigation
- Distributed execution
- Hosted server or REST API
- LangSmith integration
- LangChain dependency
- Token streaming from LLM providers
- Redis or Postgres checkpoint savers
- Complex serialization of LangChain message classes
- Graph visualization

### Examples and tests

The current milestone keeps examples in the test suite:

- `tests/test_imports.py` protects import compatibility.
- `tests/test_sequence.py` protects the docs-style sequential graph behavior.

Standalone files under `examples/` are planned for a later milestone.

### Development

```bash
pytest -q
ruff check .
```

<a id="zh-cn"></a>

## 中文

一个小而可读的 LangGraph 风格图运行时，用来学习和快速实验 agent 编排。

```python
from nano_agentgraph.graph import StateGraph, START, END
from nano_agentgraph.types import Command, interrupt
```

nano-agentgraph 追求的是 API 熟悉感，而不是完整复制 LangGraph。熟悉基础
LangGraph 示例的用户，在当前支持的子集里，应该能保留类似代码结构，只把导入
前缀换成 `nano_agentgraph`。

> 这个项目不是 LangGraph 的生产级替代品。

### 安装

```bash
pip install -e ".[dev]"
```

### 30 秒示例

```python
from typing_extensions import TypedDict
from nano_agentgraph.graph import StateGraph, START, END


class State(TypedDict):
    topic: str
    joke: str


def refine_topic(state: State):
    return {"topic": state["topic"] + " and cats"}


def generate_joke(state: State):
    return {"joke": f"This is a joke about {state['topic']}"}


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
```

### 导入映射

| LangGraph | nano-agentgraph |
|---|---|
| `from langgraph.graph import StateGraph, START, END` | `from nano_agentgraph.graph import StateGraph, START, END` |
| `from langgraph.types import Command, interrupt` | `from nano_agentgraph.types import Command, interrupt` |
| `from langgraph.checkpoint.memory import InMemorySaver` | `from nano_agentgraph.checkpoint.memory import InMemorySaver` |

也支持顶层便捷导入：

```python
from nano_agentgraph import StateGraph, START, END, Command, interrupt, InMemorySaver
```

### 当前支持范围

| 功能 | 状态 |
|---|---|
| `StateGraph(state_schema)` | 已支持 |
| `START` 和 `END` | 已支持 |
| `add_node(name, fn)` | 已支持 |
| `add_node(fn)` 节点名推断 | 已支持 |
| `add_edge(source, target)` | 已支持一条顺序路径 |
| `set_entry_point(name)` | 已支持 |
| `set_finish_point(name)` | 已支持 |
| `compile()` | 已支持顺序图 |
| `CompiledStateGraph.invoke(input)` | 已支持 |
| 局部 dict 更新 | 已支持，默认覆盖 |
| 保护调用方输入状态不被原地修改 | 已支持 |
| 从 `typing.Annotated` 解析 reducer | 计划中 |
| 条件边 | 计划中 |
| `Command(update=..., goto=...)` 路由 | 计划中 |
| 内存 checkpoint | 计划中 |
| interrupt 和 resume | 计划中 |
| streaming | 计划中 |

尚未支持的高级功能会抛出清晰的 `NotImplementedError` 或项目专用校验错误。

### 首个版本的非目标

- 完整 LangGraph API 兼容
- 真实 Pregel 并行 superstep
- 子图和父图导航
- 分布式执行
- 托管服务或 REST API
- LangSmith 集成
- LangChain 依赖
- LLM token streaming
- Redis 或 Postgres checkpoint saver
- LangChain message class 的复杂序列化
- 图可视化

### 示例和测试

当前里程碑先把示例行为放在测试中：

- `tests/test_imports.py` 保护导入兼容。
- `tests/test_sequence.py` 保护文档风格的顺序图行为。

独立的 `examples/` 文件夹会在后续里程碑补上。

### 开发

```bash
pytest -q
ruff check .
```
