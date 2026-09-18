import { useEffect, useRef, useState, type FormEvent } from 'react';
import { ArrowDown, ArrowUpRight, Clock3, Loader2, Paperclip, Plus, Send, Sparkles } from 'lucide-react';
import { ChatMessage } from '../components/assistant/ChatMessage';
import { ConversationHistoryModal } from '../components/assistant/ConversationHistoryModal';
import { useChat } from '../hooks/useChat';

const suggestions = [
  'Which quarter had the highest spending?',
  'Which department spent the most?',
  'Show the top 5 suppliers by procurement value.',
  'What are the top categories by spend?',
];

export function AssistantPage() {
  const {
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
  } = useChat();
  const [input, setInput] = useState('');
  const [historyOpen, setHistoryOpen] = useState(false);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const scrollArea = useRef<HTMLDivElement>(null);
  const composer = useRef<HTMLTextAreaElement>(null);
  const stickToBottom = useRef(true);

  useEffect(() => {
    if (stickToBottom.current && scrollArea.current) {
      scrollArea.current.scrollTop = scrollArea.current.scrollHeight;
    }
  }, [turns]);

  useEffect(() => {
    if (!isStreaming && !historyOpen) composer.current?.focus();
  }, [historyOpen, isStreaming]);

  function startNewConversation() {
    newConversation();
    setInput('');
    setHistoryOpen(false);
    stickToBottom.current = true;
    setShowScrollButton(false);
    composer.current?.focus();
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!input.trim() || isStreaming || isLoadingMessages) return;
    stickToBottom.current = true;
    setShowScrollButton(false);
    void sendMessage(input);
    setInput('');
  }

  return (
    <section className="relative flex h-full min-h-0 flex-col bg-[#fbfcfe]" aria-label="Procurement assistant">
      <div className="fixed right-16 top-6 z-30 flex items-center gap-2 sm:right-20 xl:right-[294px]">
        <button type="button" onClick={() => setHistoryOpen(true)} className="inline-flex h-11 items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-700 shadow-sm transition hover:border-slate-300 hover:bg-slate-50 sm:px-5 sm:text-sm">
          <Clock3 className="h-[18px] w-[18px]" />
          <span className="hidden sm:inline">History</span>
        </button>
        <button type="button" onClick={startNewConversation} disabled={isStreaming || isLoadingMessages} className="inline-flex h-11 items-center justify-center gap-2 rounded-lg bg-emerald px-3 text-xs font-semibold text-white shadow-sm transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50 sm:px-5 sm:text-sm">
          <Plus className="h-[18px] w-[18px]" />
          <span className="hidden sm:inline">New chat</span>
        </button>
      </div>

      <ConversationHistoryModal
        open={historyOpen}
        conversations={conversations}
        activeConversationId={activeConversationId}
        loading={isLoadingMessages || isStreaming}
        deletingConversationId={deletingConversationId}
        error={historyError}
        onClose={() => setHistoryOpen(false)}
        onOpenConversation={(id) => {
          void openConversation(id);
          setHistoryOpen(false);
          stickToBottom.current = true;
        }}
        onDeleteConversation={deleteConversation}
      />

      <div className="relative min-h-0 flex-1">
        <div
          ref={scrollArea}
          onScroll={() => {
            const element = scrollArea.current;
            if (!element) return;
            stickToBottom.current = element.scrollHeight - element.scrollTop - element.clientHeight < 100;
            setShowScrollButton(!stickToBottom.current);
          }}
          className="h-full overflow-y-auto overscroll-contain px-4 py-9 sm:px-7"
          role="region"
          aria-label="Chat messages"
          tabIndex={0}
        >
          {isLoadingMessages ? (
            <div className="flex min-h-full items-center justify-center gap-2 text-sm text-slate-500">
              <Loader2 className="h-4 w-4 animate-spin text-emerald" />Loading conversation…
            </div>
          ) : turns.length === 0 ? (
            <div className="mx-auto flex min-h-full max-w-2xl flex-col items-center justify-center py-10 text-center">
              <span className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50 text-emerald">
                <Sparkles className="h-7 w-7" />
              </span>
              <h2 className="text-2xl font-bold tracking-[-0.025em] text-slate-950">What would you like to explore?</h2>
              <p className="mt-3 max-w-md text-sm leading-6 text-slate-500">Ask questions about procurement spending, suppliers, departments, categories, and trends.</p>
              <div className="mt-8 grid w-full gap-3 text-left sm:grid-cols-2">
                {suggestions.map((prompt) => (
                  <button type="button" key={prompt} onClick={() => { setInput(prompt); composer.current?.focus(); }} className="group flex items-start justify-between gap-3 rounded-xl border border-slate-200 bg-white p-4 text-left text-xs leading-5 text-slate-600 shadow-sm transition hover:border-blue-300 hover:text-slate-900">
                    <span>{prompt}</span>
                    <ArrowUpRight className="h-4 w-4 shrink-0 text-slate-400 transition group-hover:text-blue" />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="mx-auto max-w-[960px] space-y-8 pb-5">
              {turns.map((turn, index) => (
                <ChatMessage
                  key={turn.id}
                  turn={turn}
                  canRetry={!isStreaming && index === turns.length - 1}
                  onRetry={() => { stickToBottom.current = true; void sendMessage(turn.question, turn.id); }}
                />
              ))}
            </div>
          )}
        </div>

        {showScrollButton && (
          <button type="button" onClick={() => { stickToBottom.current = true; scrollArea.current?.scrollTo({ top: scrollArea.current.scrollHeight }); setShowScrollButton(false); }} className="absolute bottom-4 left-1/2 flex -translate-x-1/2 items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600 shadow-md">
            <ArrowDown className="h-3.5 w-3.5" />Latest message
          </button>
        )}
      </div>

      <footer className="shrink-0 border-t border-slate-200 bg-white px-4 py-4 sm:px-7">
        <form onSubmit={submit} className="flex w-full items-center gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2 shadow-sm transition focus-within:border-blue-300 focus-within:ring-2 focus-within:ring-blue-100">
          <button type="button" disabled className="flex h-9 w-9 shrink-0 cursor-not-allowed items-center justify-center rounded-lg text-slate-500" aria-label="File attachments are not supported yet" title="File attachments are not supported yet">
            <Paperclip className="h-5 w-5" />
          </button>
          <label htmlFor="chat-question" className="sr-only">Your procurement question</label>
          <textarea
            ref={composer}
            id="chat-question"
            value={input}
            disabled={isLoadingMessages}
            maxLength={4000}
            rows={1}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
                event.preventDefault();
                event.currentTarget.form?.requestSubmit();
              }
            }}
            placeholder={turns.length ? 'Ask a follow-up question...' : 'Ask anything about procurement data...'}
            className="max-h-28 min-h-9 flex-1 resize-none bg-transparent py-2 text-sm leading-5 text-slate-800 outline-none placeholder:text-slate-400"
            aria-describedby="chat-composer-hint"
          />
          <button type="submit" disabled={!input.trim() || isStreaming || isLoadingMessages} aria-label={isStreaming ? 'Response in progress' : 'Send question'} className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald text-white shadow-sm transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-40">
            {isStreaming ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </button>
        </form>
        <p id="chat-composer-hint" className="mt-2 px-1 text-[10px] text-slate-400">
          {isStreaming ? 'Working on your question. You can draft your next message.' : 'Press Enter to send • Shift + Enter for a new line'}
        </p>
      </footer>
    </section>
  );
}
