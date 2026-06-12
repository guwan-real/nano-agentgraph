export const START = "__start__";
export const END = "__end__";

const ANNOTATION = Symbol("nano-agentgraph.annotation");
const ROOT = Symbol("nano-agentgraph.annotation.root");

export function Annotation(options = {}) {
  return {
    [ANNOTATION]: true,
    reducer: options.reducer,
    default: options.default,
  };
}

Annotation.Root = function Root(channels) {
  return {
    [ROOT]: true,
    channels: { ...channels },
  };
};

export class StateGraph {
  constructor(stateSchema = undefined) {
    this.stateSchema = stateSchema;
    this.nodes = new Map();
    this.edges = new Map();
    this.conditionalEdges = new Map();
  }

  addNode(nameOrFn, maybeFn) {
    const [name, fn] = this.#normalizeNode(nameOrFn, maybeFn);
    if (name === START || name === END) {
      throw new Error(`${name} is reserved and cannot be used as a node name.`);
    }
    if (this.nodes.has(name)) {
      throw new Error(`Node ${JSON.stringify(name)} already exists.`);
    }
    this.nodes.set(name, fn);
    return this;
  }

  addEdge(source, target) {
    if (source === END) {
      throw new Error("END cannot be used as an edge source.");
    }
    if (target === START) {
      throw new Error("START cannot be used as an edge target.");
    }
    if (!this.edges.has(source)) {
      this.edges.set(source, []);
    }
    this.edges.get(source).push(target);
    return this;
  }

  addConditionalEdges(source, path, pathMap = undefined) {
    if (source === START || source === END) {
      throw new Error("Conditional edges must start from a real node.");
    }
    if (typeof path !== "function") {
      throw new TypeError("Conditional edge path must be a function.");
    }
    if (this.conditionalEdges.has(source)) {
      throw new Error(`Conditional edges for ${JSON.stringify(source)} already exist.`);
    }
    this.conditionalEdges.set(source, {
      path,
      pathMap: pathMap ? { ...pathMap } : undefined,
    });
    return this;
  }

  compile() {
    this.#validate();
    return new CompiledStateGraph({
      nodes: new Map(this.nodes),
      edges: copyEdgeMap(this.edges),
      conditionalEdges: new Map(this.conditionalEdges),
      reducers: parseReducers(this.stateSchema),
      defaults: parseDefaults(this.stateSchema),
    });
  }

  #normalizeNode(nameOrFn, maybeFn) {
    if (maybeFn === undefined) {
      if (typeof nameOrFn !== "function") {
        throw new TypeError("addNode(name) requires a function as the second argument.");
      }
      if (!nameOrFn.name) {
        throw new TypeError("Cannot infer a node name; use addNode(name, fn).");
      }
      return [nameOrFn.name, nameOrFn];
    }
    if (typeof nameOrFn !== "string") {
      throw new TypeError("addNode(fn, extra) is invalid; use addNode(name, fn).");
    }
    if (typeof maybeFn !== "function") {
      throw new TypeError(`Node ${JSON.stringify(nameOrFn)} must be a function.`);
    }
    return [nameOrFn, maybeFn];
  }

  #validate() {
    if (!this.edges.has(START) || this.edges.get(START).length === 0) {
      throw new Error("Graph must have an edge from START to an entry node.");
    }

    for (const [source, targets] of this.edges) {
      if (source !== START && !this.nodes.has(source)) {
        throw new Error(`Edge source ${JSON.stringify(source)} is not a known node.`);
      }
      if (targets.length > 1) {
        throw new Error(
          `Node ${JSON.stringify(source)} has multiple outgoing edges; parallel routing is not implemented yet.`,
        );
      }
      for (const target of targets) {
        if (target !== END && !this.nodes.has(target)) {
          throw new Error(`Edge target ${JSON.stringify(target)} is not a known node.`);
        }
      }
    }

    for (const [source, { pathMap }] of this.conditionalEdges) {
      if (!this.nodes.has(source)) {
        throw new Error(`Conditional edge source ${JSON.stringify(source)} is not a known node.`);
      }
      if (this.edges.has(source)) {
        throw new Error(
          `Node ${JSON.stringify(source)} cannot have both static and conditional routing.`,
        );
      }
      if (!pathMap) {
        continue;
      }
      for (const target of Object.values(pathMap)) {
        if (target === START) {
          throw new Error("START cannot be used as a conditional edge target.");
        }
        if (target !== END && !this.nodes.has(target)) {
          throw new Error(`Conditional edge target ${JSON.stringify(target)} is not a known node.`);
        }
      }
    }
  }
}

export class CompiledStateGraph {
  constructor({ nodes, edges, conditionalEdges, reducers, defaults }) {
    this.nodes = nodes;
    this.edges = edges;
    this.conditionalEdges = conditionalEdges;
    this.reducers = reducers;
    this.defaults = defaults;
  }

  async invoke(input, config = {}) {
    let state = { ...applyDefaults(this.defaults), ...input };
    let current = nextStatic(this.edges, START);
    const recursionLimit = normalizeRecursionLimit(config.recursionLimit ?? 25);
    let steps = 0;

    while (current !== END) {
      if (recursionLimit !== null && steps >= recursionLimit) {
        throw new Error(`Graph execution exceeded recursionLimit=${recursionLimit}.`);
      }

      const update = await this.nodes.get(current)({ ...state });
      if (!isPlainObject(update)) {
        throw new TypeError(`Node ${JSON.stringify(current)} must return a plain object update.`);
      }
      state = mergeState(state, update, this.reducers);
      current = await this.#selectNext(current, state);
      steps += 1;
    }

    return state;
  }

  async #selectNext(source, state) {
    const conditional = this.conditionalEdges.get(source);
    if (conditional) {
      const route = await conditional.path({ ...state });
      return resolveRoute(route, conditional.pathMap, this.nodes);
    }
    return nextStatic(this.edges, source);
  }
}

function copyEdgeMap(edges) {
  return new Map([...edges].map(([source, targets]) => [source, [...targets]]));
}

function parseReducers(schema) {
  const reducers = new Map();
  for (const [key, annotation] of Object.entries(rootChannels(schema))) {
    if (annotation?.[ANNOTATION] && typeof annotation.reducer === "function") {
      reducers.set(key, annotation.reducer);
    }
  }
  return reducers;
}

function parseDefaults(schema) {
  const defaults = new Map();
  for (const [key, annotation] of Object.entries(rootChannels(schema))) {
    if (annotation?.[ANNOTATION] && typeof annotation.default === "function") {
      defaults.set(key, annotation.default);
    }
  }
  return defaults;
}

function rootChannels(schema) {
  if (schema?.[ROOT]) {
    return schema.channels;
  }
  return {};
}

function applyDefaults(defaults) {
  const state = {};
  for (const [key, defaultFn] of defaults) {
    state[key] = defaultFn();
  }
  return state;
}

function mergeState(state, update, reducers) {
  const next = { ...state };
  for (const [key, value] of Object.entries(update)) {
    if (reducers.has(key) && Object.hasOwn(next, key)) {
      next[key] = reducers.get(key)(next[key], value);
    } else {
      next[key] = value;
    }
  }
  return next;
}

function nextStatic(edges, source) {
  const targets = edges.get(source);
  if (!targets?.length) {
    throw new Error(
      `Node ${JSON.stringify(source)} has no route. Add a static edge or conditional edge.`,
    );
  }
  return targets[0];
}

function resolveRoute(route, pathMap, nodes) {
  if (Array.isArray(route)) {
    throw new Error("Parallel routing is not implemented yet.");
  }
  const target = pathMap ? pathMap[route] : route;
  if (typeof target !== "string") {
    throw new Error(`Route target must be a node name or END, got ${String(target)}.`);
  }
  if (target !== END && !nodes.has(target)) {
    throw new Error(`Route target ${JSON.stringify(target)} is not a known node.`);
  }
  return target;
}

function normalizeRecursionLimit(limit) {
  if (limit === null) {
    return null;
  }
  if (!Number.isInteger(limit) || limit < 1) {
    throw new Error("config.recursionLimit must be a positive integer or null.");
  }
  return limit;
}

function isPlainObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}
