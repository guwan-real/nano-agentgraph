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
| Reducers from `typing.Annotated` | Supported |
| Conditional edges | Supported for one destination |
| `Command(update=..., goto=...)` routing | Supported for one destination |
| In-memory checkpointing | Supported |
| `get_state(config)` / `update_state(config, values)` | Supported |
| Interrupt and resume | Supported with checkpointing |
| `stream_mode="values"` / `stream_mode="updates"` | Supported |

Unsupported advanced features, such as parallel routing and message streaming,
raise clear `NotImplementedError` or project-specific validation errors.

When resuming from `interrupt(...)`, the interrupted node restarts from the
beginning and receives the resume value from the next `interrupt(...)` call.

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

Runnable examples live in `examples/`:

- `examples/01_sequence.py`
- `examples/02_conditional.py`
- `examples/03_reducers.py`
- `examples/04_command.py`
- `examples/05_checkpoint.py`
- `examples/06_interrupt_resume.py`
- `examples/07_streaming.py`

The test suite covers the same public behavior:

- `tests/test_imports.py` protects import compatibility.
- `tests/test_sequence.py` protects the docs-style sequential graph behavior.
- `tests/test_reducers.py` covers `typing.Annotated` reducers.
- `tests/test_conditional_edges.py` covers conditional routing.
- `tests/test_command.py` covers `Command(update=..., goto=...)`.
- `tests/test_checkpoint_memory.py` covers `InMemorySaver` and state snapshots.
- `tests/test_interrupt_resume.py` covers interrupt/resume.
- `tests/test_streaming.py` covers `values` and `updates` streaming.

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
| 从 `typing.Annotated` 解析 reducer | 已支持 |
| 条件边 | 已支持单目标 |
| `Command(update=..., goto=...)` 路由 | 已支持单目标 |
| 内存 checkpoint | 已支持 |
| `get_state(config)` / `update_state(config, values)` | 已支持 |
| interrupt 和 resume | 已支持，需 checkpoint |
| `stream_mode="values"` / `stream_mode="updates"` | 已支持 |

尚未支持的高级功能，例如并行路由和 message streaming，会抛出清晰的
`NotImplementedError` 或项目专用校验错误。

从 `interrupt(...)` 恢复时，被中断的节点会从头重新执行，并在下一次
`interrupt(...)` 调用处收到 resume 值。

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

可运行示例位于 `examples/`：

- `examples/01_sequence.py`
- `examples/02_conditional.py`
- `examples/03_reducers.py`
- `examples/04_command.py`
- `examples/05_checkpoint.py`
- `examples/06_interrupt_resume.py`
- `examples/07_streaming.py`

测试套件覆盖同一组公开行为：

- `tests/test_imports.py` 保护导入兼容。
- `tests/test_sequence.py` 保护文档风格的顺序图行为。
- `tests/test_reducers.py` 覆盖 `typing.Annotated` reducer。
- `tests/test_conditional_edges.py` 覆盖条件路由。
- `tests/test_command.py` 覆盖 `Command(update=..., goto=...)`。
- `tests/test_checkpoint_memory.py` 覆盖 `InMemorySaver` 和状态快照。
- `tests/test_interrupt_resume.py` 覆盖 interrupt/resume。
- `tests/test_streaming.py` 覆盖 `values` 和 `updates` streaming。

### 开发

```bash
pytest -q
ruff check .
```
