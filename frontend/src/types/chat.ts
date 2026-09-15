export type Pipeline = Record<string, unknown>[];
export type ChatStep = 'route_question' | 'generate_direct_response' | 'generate_query' | 'validate_query' | 'correct_query' | 'execute_query' | 'generate_answer';
export type StepStatus = 'running' | 'complete' | 'error';

export interface ChatResponse {
  conversation_id: string;
  answer: string;
  query_description: string | null;
  pipeline: Pipeline | null;
  result_count: number;
  retry_count: number;
}

export interface ChatProgress {
  step: ChatStep;
  status: StepStatus;
  label: string;
}

export type ChatEvent =
  | { type: 'start'; conversation_id: string }
  | ({ type: 'progress' } & ChatProgress)
  | { type: 'query'; pipeline: Pipeline; query_description: string; retry_count: number }
  | { type: 'answer_delta'; text: string }
  | ({ type: 'done' } & ChatResponse)
  | { type: 'error'; message: string };

export interface ChatTurn {
  id: string;
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
  error?: string;
}

export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface StoredMessage {
  id: string;
  conversation_id: string;
  turn_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  query_description: string | null;
  pipeline: Pipeline | null;
  result_count: number;
  retry_count: number;
}

export interface ConversationMessages {
  conversation: ConversationSummary;
  messages: StoredMessage[];
}
