import type { ChatEvent, ConversationMessages, ConversationSummary } from '../types/chat';

const AI_API_URL = import.meta.env.VITE_AI_API_URL ?? '';

export class ChatServiceError extends Error {
  constructor(
    message: string,
    readonly details?: { code: string; stage: string; message: string; retryable: boolean },
  ) {
    super(message);
    this.name = 'ChatServiceError';
  }
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${AI_API_URL}${path}`, { signal });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: unknown; error?: { code: string; stage: string; message: string; retryable: boolean } } | null;
    throw new ChatServiceError(body?.error?.message ?? (typeof body?.detail === 'string' ? body.detail : `The request failed (${response.status}).`), body?.error);
  }
  return response.json() as Promise<T>;
}

export function fetchConversations(signal?: AbortSignal): Promise<ConversationSummary[]> {
  return getJson('/api/chat/conversations', signal);
}

export function fetchConversation(conversationId: string, signal?: AbortSignal): Promise<ConversationMessages> {
  return getJson(`/api/chat/conversations/${encodeURIComponent(conversationId)}`, signal);
}

export async function deleteConversation(conversationId: string): Promise<void> {
  const response = await fetch(
    `${AI_API_URL}/api/chat/conversations/${encodeURIComponent(conversationId)}`,
    { method: 'DELETE' },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: unknown; error?: { code: string; stage: string; message: string; retryable: boolean } } | null;
    throw new Error(
      typeof body?.detail === 'string'
        ? body.detail
        : `Could not delete the conversation (${response.status}).`,
    );
  }
}

/** Decode SSE frames across arbitrary network and UTF-8 chunk boundaries. */
export async function consumeChatStream(
  body: ReadableStream<Uint8Array>,
  onEvent: (event: ChatEvent) => void,
): Promise<void> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let completed = false;

  function dispatch(frame: string) {
    const data = frame.split('\n')
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).trimStart()).join('\n');
    if (!data) return; // Heartbeat or SSE metadata.
    let event: ChatEvent;
    try {
      event = JSON.parse(data) as ChatEvent;
    } catch {
      throw new ChatServiceError(
        'The assistant stream was interrupted. Please try again.',
        { code: 'STREAM_INTERRUPTED', stage: 'stream', message: 'The assistant stream was interrupted. Please try again.', retryable: true },
      );
    }
    if (event.type === 'error') throw new ChatServiceError(event.error?.message ?? event.message, event.error);
    onEvent(event);
    if (event.type === 'done') completed = true;
  }

  try {
    while (!completed) {
      const { done, value } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      // Normalize CRLF only once the LF arrives, including split CRLF chunks.
      buffer = buffer.replace(/\r\n/g, '\n');
      let boundary: number;
      while (!completed && (boundary = buffer.indexOf('\n\n')) >= 0) {
        dispatch(buffer.slice(0, boundary));
        buffer = buffer.slice(boundary + 2);
      }
      if (done) {
        if (!completed) throw new Error('The connection closed before the response finished. Please try again.');
        break;
      }
    }
  } finally {
    await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}

export async function streamChat(
  message: string,
  conversationId: string | undefined,
  onEvent: (event: ChatEvent) => void,
  signal: AbortSignal,
  requestId: string = crypto.randomUUID(),
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${AI_API_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        'X-Request-ID': requestId,
      },
      body: JSON.stringify({ message, conversation_id: conversationId }),
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error;
    throw new ChatServiceError(
      'Unable to reach the assistant service. Please try again.',
      { code: 'AI_SERVICE_UNAVAILABLE', stage: 'connection', message: 'Unable to reach the assistant service. Please try again.', retryable: true },
    );
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: unknown; error?: { code: string; stage: string; message: string; retryable: boolean } } | null;
    throw new ChatServiceError(body?.error?.message ?? (typeof body?.detail === 'string' ? body.detail : `The assistant request failed (${response.status}). Please try again.`), body?.error);
  }
  if (!response.body || !response.headers.get('content-type')?.includes('text/event-stream')) {
    throw new Error('The server did not return a chat stream. Please check that the AI service is running.');
  }
  await consumeChatStream(response.body, onEvent);
}
