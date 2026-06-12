export declare const START: "__start__";
export declare const END: "__end__";

export type Reducer<T> = (left: T, right: T) => T;

export type AnnotationSpec<T = unknown> = {
  reducer?: Reducer<T>;
  default?: () => T;
};

export type AnnotationChannel<T = unknown> = AnnotationSpec<T> & {
  readonly __brand?: "Annotation";
};

export type AnyAnnotationChannel = AnnotationChannel<any>;

export type AnnotationRoot<TChannels extends Record<string, AnyAnnotationChannel>> = {
  channels: TChannels;
  readonly __brand?: "AnnotationRoot";
};

export declare function Annotation<T = unknown>(
  options?: AnnotationSpec<T>,
): AnnotationChannel<T>;

export declare namespace Annotation {
  function Root<TChannels extends Record<string, AnyAnnotationChannel>>(
    channels: TChannels,
  ): AnnotationRoot<TChannels>;
}

export type NodeFunction<TState extends object> = (
  state: Readonly<TState>,
) => Partial<TState> | Promise<Partial<TState>>;

export type RouteFunction<TState extends object> = (
  state: Readonly<TState>,
) => string | Promise<string>;

export declare class StateGraph<TState extends object = Record<string, unknown>> {
  constructor(stateSchema?: AnnotationRoot<Record<string, AnyAnnotationChannel>> | unknown);
  addNode(name: string, fn: NodeFunction<TState>): this;
  addNode(fn: NodeFunction<TState> & { name: string }): this;
  addEdge(source: string, target: string): this;
  addConditionalEdges(
    source: string,
    path: RouteFunction<TState>,
    pathMap?: Record<string, string>,
  ): this;
  compile(): CompiledStateGraph<TState>;
}

export type InvokeConfig = {
  recursionLimit?: number | null;
};

export declare class CompiledStateGraph<
  TState extends object = Record<string, unknown>,
> {
  invoke(input: Partial<TState>, config?: InvokeConfig): Promise<TState>;
}
