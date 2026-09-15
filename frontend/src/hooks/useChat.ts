import { useEffect, useRef, useState } from 'react';
import { fetchConversation, fetchConversations, streamChat } from '../services/chatService';
import type { ChatEvent, ChatTurn, ConversationSummary, StoredMessage } from '../types/chat';

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

function messagesToTurns(messages: StoredMessage[]): ChatTurn[] {
  const turns = new Map<string, ChatTurn>();

  for (const message of messages) {
    if (message.role === 'user') {
      turns.set(message.turn_id, {
        id: message.turn_id,
        question: message.content,
        createdAt: message.created_at,
        answer: '',
        status: 'complete',
        progress: [],
        pipeline: null,
        queryDescription: null,
        retryCount: 0,
      });
      continue;
    }

    const turn = turns.get(message.turn_id);
    if (turn) {
      turns.set(message.turn_id, {
        ...turn,
        answer: message.content,
        pipeline: message.pipeline,
        queryDescription: message.query_description,
        queryGeneratedAt: message.pipeline ? message.created_at : undefined,
        resultCount: message.result_count,
        retryCount: message.retry_count,
      });
    }
  }

  return [...turns.values()];
}

export function useChat() {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string>();
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [historyError, setHistoryError] = useState<string>();
  const conversationId = useRef<string | undefined>(undefined);
  const activeRequest = useRef<AbortController | null>(null);
  const historyRequest = useRef<AbortController | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchConversations(controller.signal)
      .then(setConversations)
      .catch((error: unknown) => {
        if (!controller.signal.aborted) setHistoryError(error instanceof Error ? error.message : 'Could not load chat history.');
      });
    return () => {
      controller.abort();
      activeRequest.current?.abort();
      historyRequest.current?.abort();
      activeRequest.current = null;
    };
  }, []);

  async function refreshConversations() {
    try {
      setConversations(await fetchConversations());
      setHistoryError(undefined);
    } catch (error) {
      setHistoryError(error instanceof Error ? error.message : 'Could not load chat history.');
    }
  }

  async function openConversation(id: string) {
    if (activeRequest.current || id === conversationId.current) return;
    historyRequest.current?.abort();
    const controller = new AbortController();
    historyRequest.current = controller;
    setIsLoadingMessages(true);
    setHistoryError(undefined);
    try {
      const result = await fetchConversation(id, controller.signal);
      if (historyRequest.current !== controller) return;
      conversationId.current = result.conversation.id;
      setActiveConversationId(result.conversation.id);
      setTurns(messagesToTurns(result.messages));
    } catch (error) {
      if (!controller.signal.aborted) setHistoryError(error instanceof Error ? error.message : 'Could not load this conversation.');
    } finally {
      if (historyRequest.current === controller) {
        historyRequest.current = null;
        setIsLoadingMessages(false);
      }
    }
  }

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
        // The server persists the turn before "done". Do not adopt a new ID
        // earlier, or a failed first request would point at an unsaved chat.
        if (event.type === 'done') {
          conversationId.current = event.conversation_id;
          setActiveConversationId(event.conversation_id);
        }
        setTurns((current) => current.map((item) => item.id === turn.id ? applyEvent(item, event) : item));
        if (event.type === 'done') void refreshConversations();
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
    historyRequest.current?.abort();
    historyRequest.current = null;
    conversationId.current = undefined;
    setActiveConversationId(undefined);
    setTurns([]);
    setIsLoadingMessages(false);
    setHistoryError(undefined);
  }

  return {
    turns,
    conversations,
    activeConversationId,
    isStreaming,
    isLoadingMessages,
    historyError,
    sendMessage,
    openConversation,
    newConversation,
  };
}
