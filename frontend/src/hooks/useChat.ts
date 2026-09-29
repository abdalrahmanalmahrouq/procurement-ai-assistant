import { useCallback, useEffect, useRef, useState } from 'react';
import {
  deleteConversation as deleteConversationRequest,
  fetchConversation,
  fetchConversations,
  streamChat,
  ChatServiceError,
} from '../services/chatService';
import type { ChatEvent, ChatTurn, ConversationSummary, StoredMessage } from '../types/chat';

const ACTIVE_CONVERSATION_KEY = 'procurement-ai-assistant.activeConversationId';

function readActiveConversationId(): string | undefined {
  try {
    return window.localStorage.getItem(ACTIVE_CONVERSATION_KEY) || undefined;
  } catch {
    // The assistant still works when storage is disabled by the browser.
    return undefined;
  }
}

function persistActiveConversationId(id?: string) {
  try {
    if (id) window.localStorage.setItem(ACTIVE_CONVERSATION_KEY, id);
    else window.localStorage.removeItem(ACTIVE_CONVERSATION_KEY);
  } catch {
    // Treat storage as an optional enhancement (for example, in private mode).
  }
}

function applyEvent(turn: ChatTurn, event: ChatEvent): ChatTurn {
  switch (event.type) {
    case 'start':
      return { ...turn, requestId: event.request_id };
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
    case 'visualization':
      return { ...turn, visualization: event.visualization };
    case 'done':
      return {
        ...turn, requestId: event.request_id, status: 'complete', answer: event.answer, pipeline: event.pipeline,
        queryDescription: event.query_description, resultCount: event.result_count, retryCount: event.retry_count,
        visualization: event.visualization,
      };
    default:
      return turn;
  }
}

function messagesToTurns(messages: StoredMessage[]): ChatTurn[] {
  const turns = new Map<string, ChatTurn>();

  for (const message of messages) {
    if (message.role === 'user') {
      const failed = message.status === 'error' || message.status === 'pending';
      turns.set(message.turn_id, {
        id: message.turn_id,
        requestId: message.request_id ?? undefined,
        question: message.content,
        createdAt: message.created_at,
        answer: '',
        status: failed ? 'error' : 'complete',
        progress: [],
        pipeline: null,
        queryDescription: null,
        retryCount: 0,
        visualization: null,
        error: failed ? 'The previous assistant response did not finish. Please try again.' : undefined,
      });
      continue;
    }

    const turn = turns.get(message.turn_id);
    if (turn) {
      const failed = message.status === 'error';
      turns.set(message.turn_id, {
        ...turn,
        answer: failed ? '' : message.content,
        status: failed ? 'error' : 'complete',
        error: failed ? message.content : undefined,
        pipeline: message.pipeline,
        queryDescription: message.query_description,
        queryGeneratedAt: message.pipeline ? message.created_at : undefined,
        resultCount: message.result_count,
        retryCount: message.retry_count,
        visualization: message.visualization,
      });
    }
  }

  return [...turns.values()];
}

export function useChat() {
  const [initialConversationId] = useState(readActiveConversationId);
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | undefined>(initialConversationId);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(Boolean(initialConversationId));
  const [deletingConversationId, setDeletingConversationId] = useState<string>();
  const [historyError, setHistoryError] = useState<string>();
  const conversationId = useRef<string | undefined>(initialConversationId);
  const activeRequest = useRef<AbortController | null>(null);
  const historyRequest = useRef<AbortController | null>(null);

  const setCurrentConversation = useCallback((id?: string) => {
    conversationId.current = id;
    setActiveConversationId(id);
    persistActiveConversationId(id);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchConversations(controller.signal)
      .then(setConversations)
      .catch((error: unknown) => {
        if (!controller.signal.aborted) setHistoryError(error instanceof Error ? error.message : 'Could not load chat history.');
      });

    const savedConversationId = conversationId.current;
    if (savedConversationId) {
      fetchConversation(savedConversationId, controller.signal)
        .then((result) => {
          if (controller.signal.aborted) return;
          setCurrentConversation(result.conversation.id);
          setTurns(messagesToTurns(result.messages));
          setHistoryError(undefined);
        })
        .catch((error: unknown) => {
          if (controller.signal.aborted) return;
          // Do not keep retrying a stale ID on every future page refresh.
          setCurrentConversation(undefined);
          setHistoryError(error instanceof Error ? error.message : 'Could not restore the previous conversation.');
        })
        .finally(() => {
          if (!controller.signal.aborted) setIsLoadingMessages(false);
        });
    }

    return () => {
      controller.abort();
      activeRequest.current?.abort();
      historyRequest.current?.abort();
      activeRequest.current = null;
    };
  }, [setCurrentConversation]);

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
      setCurrentConversation(result.conversation.id);
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

  async function deleteConversation(id: string) {
    if (activeRequest.current || deletingConversationId) return false;
    setDeletingConversationId(id);
    setHistoryError(undefined);
    try {
      await deleteConversationRequest(id);
      setConversations((current) => current.filter((item) => item.id !== id));
      if (conversationId.current === id) {
        historyRequest.current?.abort();
        historyRequest.current = null;
        setCurrentConversation(undefined);
        setTurns([]);
        setIsLoadingMessages(false);
      }
      return true;
    } catch (error) {
      setHistoryError(
        error instanceof Error
          ? error.message
          : 'Could not delete this conversation.',
      );
      return false;
    } finally {
      setDeletingConversationId(undefined);
    }
  }

  async function sendMessage(message: string, retryId?: string) {
    const question = message.trim();
    if (!question || question.length > 4000 || activeRequest.current) return;
    const controller = new AbortController();
    const requestId = crypto.randomUUID();
    activeRequest.current = controller;
    const turn: ChatTurn = {
      id: retryId ?? crypto.randomUUID(), requestId, question, createdAt: new Date().toISOString(),
      answer: '', status: 'streaming', progress: [], pipeline: null, queryDescription: null, retryCount: 0,
      visualization: null,
    };
    setTurns((current) => retryId ? current.map((item) => item.id === retryId ? turn : item) : [...current, turn]);
    setIsStreaming(true);
    let timedOut = false;
    const timeout = window.setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, Number(import.meta.env.VITE_CHAT_TIMEOUT_MS ?? 180_000));

    try {
      await streamChat(question, conversationId.current, (event) => {
        if (activeRequest.current !== controller) return;
        // The server persists the user message before emitting "start", so the
        // conversation remains valid even if later analytical work fails.
        if (event.type === 'start' || event.type === 'done') {
          setCurrentConversation(event.conversation_id);
        }
        setTurns((current) => current.map((item) => item.id === turn.id ? applyEvent(item, event) : item));
        if (event.type === 'done') void refreshConversations();
      }, controller.signal, requestId);
    } catch (error) {
      if (activeRequest.current !== controller) return;
      const details = error instanceof ChatServiceError ? error.details : undefined;
      const message = timedOut ? 'This request took too long. Please try again.'
        : error instanceof Error ? error.message : 'Unable to connect to the assistant. Please try again.';
      setTurns((current) => current.map((item) => item.id === turn.id ? {
        ...item, answer: '', visualization: null, status: 'error', error: message,
        errorCode: details?.code, failedStage: details?.stage, retryable: details?.retryable ?? true,
      } : item));
      if (conversationId.current) void refreshConversations();
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
    setCurrentConversation(undefined);
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
    deletingConversationId,
    historyError,
    sendMessage,
    openConversation,
    deleteConversation,
    newConversation,
  };
}
