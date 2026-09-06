import { useEffect, useRef, useState } from 'react';
import { streamChat } from '../services/chatService';
import type { ChatEvent, ChatTurn } from '../types/chat';

function applyEvent(turn: ChatTurn, event: ChatEvent): ChatTurn {
  switch (event.type) {
    case 'progress': {
      const previous = turn.progress.findIndex((item) => item.step === event.step);
      const progress = [...turn.progress];
      if (previous < 0) progress.push(event);
      else progress[previous] = event;
      return { ...turn, progress };
    }
    case 'query':
      return { ...turn, pipeline: event.pipeline, queryDescription: event.query_description, retryCount: event.retry_count, queryGeneratedAt: new Date().toISOString() };
    case 'answer_delta':
      return { ...turn, answer: turn.answer + event.text };
    case 'done':
      return {
        ...turn, status: 'complete', answer: event.answer, pipeline: event.pipeline,
        queryDescription: event.query_description, resultCount: event.result_count, retryCount: event.retry_count,
      };
    default:
      return turn;
  }
}

export function useChat() {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const conversationId = useRef<string | undefined>(undefined);
  const activeRequest = useRef<AbortController | null>(null);

  useEffect(() => () => {
    activeRequest.current?.abort();
    activeRequest.current = null;
  }, []);

  async function sendMessage(message: string, retryId?: string) {
    const question = message.trim();
    if (!question || question.length > 4000 || activeRequest.current) return;
    const controller = new AbortController();
    activeRequest.current = controller;
    const turn: ChatTurn = {
      id: retryId ?? crypto.randomUUID(), question, createdAt: new Date().toISOString(),
      answer: '', status: 'streaming', progress: [], pipeline: null, queryDescription: null, retryCount: 0,
    };
    setTurns((current) => retryId ? current.map((item) => item.id === retryId ? turn : item) : [...current, turn]);
    setIsStreaming(true);
    let timedOut = false;
    const timeout = window.setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, 180_000);

    try {
      await streamChat(question, conversationId.current, (event) => {
        if (activeRequest.current !== controller) return;
        if (event.type === 'start' || event.type === 'done') conversationId.current = event.conversation_id;
        setTurns((current) => current.map((item) => item.id === turn.id ? applyEvent(item, event) : item));
      }, controller.signal);
    } catch (error) {
      if (activeRequest.current !== controller) return;
      const message = timedOut ? 'This request took too long. Please try again.'
        : error instanceof Error ? error.message : 'Unable to connect to the assistant. Please try again.';
      setTurns((current) => current.map((item) => item.id === turn.id ? { ...item, status: 'error', error: message } : item));
    } finally {
      window.clearTimeout(timeout);
      if (activeRequest.current === controller) {
        activeRequest.current = null;
        setIsStreaming(false);
      }
    }
  }

  function newConversation() {
    if (activeRequest.current) return;
    conversationId.current = undefined;
    setTurns([]);
  }

  return { turns, isStreaming, sendMessage, newConversation };
}
