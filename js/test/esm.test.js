import assert from "node:assert/strict";
import test from "node:test";

import { Annotation, END, START, StateGraph } from "nano-agentgraph";

test("runs async sequence graphs and merges partial state", async () => {
  const graph = new StateGraph()
    .addNode("refine", async (state) => ({ topic: `${state.topic} and cats` }))
    .addNode("joke", (state) => ({ joke: `joke about ${state.topic}` }))
    .addEdge(START, "refine")
    .addEdge("refine", "joke")
    .addEdge("joke", END)
    .compile();

  assert.deepEqual(await graph.invoke({ topic: "ice cream" }), {
    topic: "ice cream and cats",
    joke: "joke about ice cream and cats",
  });
});

test("supports Annotation reducers and defaults", async () => {
  const State = Annotation.Root({
    messages: Annotation({
      reducer: (left, right) => left.concat(right),
      default: () => [],
    }),
  });

  const graph = new StateGraph(State)
    .addNode("first", () => ({ messages: ["first"] }))
    .addNode("second", () => ({ messages: ["second"] }))
    .addEdge(START, "first")
    .addEdge("first", "second")
    .addEdge("second", END)
    .compile();

  assert.deepEqual(await graph.invoke({}), {
    messages: ["first", "second"],
  });
});

test("maps conditional route values to END", async () => {
  const graph = new StateGraph()
    .addNode("router", (state) => ({ ready: state.ready }))
    .addNode("worker", () => ({ worked: true }))
    .addEdge(START, "router")
    .addConditionalEdges("router", (state) => (state.ready ? "go" : "stop"), {
      go: "worker",
      stop: END,
    })
    .addEdge("worker", END)
    .compile();

  assert.deepEqual(await graph.invoke({ ready: false }), { ready: false });
  assert.deepEqual(await graph.invoke({ ready: true }), {
    ready: true,
    worked: true,
  });
});

test("passes node errors through unchanged", async () => {
  const original = new TypeError("boom");
  const graph = new StateGraph()
    .addNode("bad", () => {
      throw original;
    })
    .addEdge(START, "bad")
    .addEdge("bad", END)
    .compile();

  await assert.rejects(graph.invoke({}), (error) => error === original);
});

test("rejects invalid recursion limits", async () => {
  const graph = new StateGraph()
    .addNode("node", () => ({}))
    .addEdge(START, "node")
    .addEdge("node", END)
    .compile();

  await assert.rejects(
    graph.invoke({}, { recursionLimit: 0 }),
    /recursionLimit/,
  );
});
