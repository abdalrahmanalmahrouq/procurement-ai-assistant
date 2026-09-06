import type { ChatEvent } from '../types/chat';

const API_URL = import.meta.env.VITE_API_URL ?? '';

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
    const event = JSON.parse(data) as ChatEvent;
    if (event.type === 'error') throw new Error(event.message);
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
): Promise<void> {
  const response = await fetch(`${API_URL}/api/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({ message, conversation_id: conversationId }),
    signal,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: unknown } | null;
    throw new Error(typeof body?.detail === 'string' ? body.detail : `The assistant request failed (${response.status}). Please try again.`);
  }
  if (!response.body || !response.headers.get('content-type')?.includes('text/event-stream')) {
    throw new Error('The server did not return a chat stream. Please check that the backend is running.');
  }
  await consumeChatStream(response.body, onEvent);
}
