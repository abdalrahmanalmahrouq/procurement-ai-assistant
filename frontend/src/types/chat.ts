export type Pipeline = Record<string, unknown>[];
export type VisualizationType = 'bar' | 'line' | 'area' | 'pie' | 'donut' | 'metric';
export type ValueFormat = 'currency' | 'number' | 'percent';

export interface VisualizationDatum {
  label: string;
  value: number;
}

export interface Visualization {
  type: VisualizationType;
  title: string;
  subtitle: string;
  x_axis_label: string;
  y_axis_label: string;
  value_format: ValueFormat;
  data: VisualizationDatum[];
}

export type ChatStep = 'route_question' | 'generate_direct_response' | 'contextual_content' | 'generate_query' | 'validate_query' | 'correct_query' | 'execute_query' | 'generate_visualization' | 'generate_answer';
export type StepStatus = 'running' | 'complete' | 'error';

export interface ChatResponse {
  request_id: string;
  conversation_id: string;
  answer: string;
  query_description: string | null;
  pipeline: Pipeline | null;
  result_count: number;
  retry_count: number;
  visualization: Visualization | null;
}

export interface ChatProgress {
  step: ChatStep;
  status: StepStatus;
  label: string;
}

export type ChatEvent =
  | { type: 'start'; request_id: string; conversation_id: string }
  | ({ type: 'progress' } & ChatProgress)
  | { type: 'query'; pipeline: Pipeline; query_description: string; retry_count: number }
  | { type: 'visualization'; visualization: Visualization }
  | { type: 'answer_delta'; text: string }
  | ({ type: 'done' } & ChatResponse)
  | { type: 'error'; request_id: string; message: string };

export interface ChatTurn {
  id: string;
  requestId?: string;
  question: string;
  createdAt: string;
  answer: string;
  status: 'streaming' | 'complete' | 'error';
  progress: ChatProgress[];
  pipeline: Pipeline | null;
  queryDescription: string | null;
  queryGeneratedAt?: string;
  resultCount?: number;
  retryCount: number;
  visualization: Visualization | null;
  error?: string;
}

export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface StoredMessage {
  id: string;
  conversation_id: string;
  turn_id: string;
  request_id: string | null;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  query_description: string | null;
  pipeline: Pipeline | null;
  result_count: number;
  retry_count: number;
  visualization: Visualization | null;
  status: 'pending' | 'complete' | 'error';
}

export interface ConversationMessages {
  conversation: ConversationSummary;
  messages: StoredMessage[];
}
