import { Annotation, END, START, StateGraph } from "nano-agentgraph";

type State = {
  messages: string[];
  done?: boolean;
};

const StateAnnotation = Annotation.Root({
  messages: Annotation<string[]>({
    reducer: (left, right) => left.concat(right),
    default: () => [],
  }),
});

const graph = new StateGraph<State>(StateAnnotation)
  .addNode("node", async () => ({ messages: ["ok"] }))
  .addConditionalEdges("node", () => "stop", { stop: END })
  .addEdge(START, "node")
  .compile();

const result = await graph.invoke({});
result.messages.push("typed");
