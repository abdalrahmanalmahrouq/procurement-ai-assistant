import { useEffect, useRef, useState, type FormEvent } from 'react';
import { ArrowDown, ArrowUpRight, Loader2, MessageSquarePlus, Send, Sparkles } from 'lucide-react';
import { ChatMessage } from '../components/assistant/ChatMessage';
import { useChat } from '../hooks/useChat';

const suggestions = [
  'Which quarter had the highest spending?',
  'Which department spent the most?',
  'Show the top 5 suppliers by procurement value.',
  'What are the top categories by spend?',
];

export function AssistantPage() {
  const { turns, isStreaming, sendMessage, newConversation } = useChat();
  const [input, setInput] = useState('');
  const [showScrollButton, setShowScrollButton] = useState(false);
  const scrollArea = useRef<HTMLDivElement>(null);
  const composer = useRef<HTMLTextAreaElement>(null);
  const stickToBottom = useRef(true);

  useEffect(() => {
    if (stickToBottom.current && scrollArea.current) scrollArea.current.scrollTop = scrollArea.current.scrollHeight;
  }, [turns]);
  useEffect(() => { if (!isStreaming) composer.current?.focus(); }, [isStreaming]);

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!input.trim() || isStreaming) return;
    stickToBottom.current = true;
    setShowScrollButton(false);
    void sendMessage(input);
    setInput('');
  }
  function choosePrompt(prompt: string) {
    setInput(prompt);
    composer.current?.focus();
  }
  return (
    <div className="mx-auto max-w-6xl">
      <section className="card flex h-[calc(100dvh-170px)] min-h-[520px] flex-col overflow-hidden" aria-label="Procurement assistant">
        <header className="flex items-center justify-between gap-3 border-b border-slate-100 px-4 py-4 sm:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald"><Sparkles className="h-5 w-5" /></span>
            <div><h1 className="text-sm font-semibold text-slate-900 sm:text-base">Procurement assistant</h1><p className="mt-0.5 text-xs text-slate-500">Ask a question. Explore the data behind the answer.</p></div>
          </div>
          <button type="button" onClick={() => { newConversation(); setInput(''); stickToBottom.current = true; setShowScrollButton(false); composer.current?.focus(); }} disabled={isStreaming || !turns.length} className="soft-button shrink-0 disabled:cursor-not-allowed disabled:opacity-40" aria-label="Start a new chat"><MessageSquarePlus className="h-4 w-4" /><span className="hidden sm:inline">New chat</span></button>
        </header>
        <div className="relative flex min-h-0 flex-1 flex-col">
          <div ref={scrollArea} onScroll={() => {
            const element = scrollArea.current;
            if (!element) return;
            stickToBottom.current = element.scrollHeight - element.scrollTop - element.clientHeight < 100;
            setShowScrollButton(!stickToBottom.current);
          }} className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-3 py-6 sm:px-6" role="region" aria-label="Chat messages" tabIndex={0}>
            {turns.length === 0 ? <div className="mx-auto flex min-h-full max-w-lg flex-col items-center justify-center py-6 text-center">
              <span className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50 text-emerald"><Sparkles className="h-7 w-7" /></span>
              <h2 className="text-xl font-semibold tracking-tight text-slate-900 sm:text-2xl">What would you like to explore?</h2>
              <p className="mt-3 max-w-sm text-sm leading-6 text-slate-500">Explore procurement spending, suppliers, and departments. Follow each query from generation to results.</p>
              <div className="mt-7 grid w-full gap-3 text-left sm:grid-cols-2">{suggestions.map((prompt) => <button type="button" key={prompt} onClick={() => choosePrompt(prompt)} className="group flex items-start justify-between gap-3 rounded-xl border border-slate-200 p-4 text-left text-xs leading-5 text-slate-600 transition hover:border-emerald/40 hover:bg-emerald-50/50 hover:text-slate-900"><span>{prompt}</span><ArrowUpRight className="h-4 w-4 shrink-0 text-slate-400 group-hover:text-emerald" /></button>)}</div>
            </div> : <div className="space-y-8">{turns.map((turn, index) => <ChatMessage key={turn.id} turn={turn} canRetry={!isStreaming && index === turns.length - 1} onRetry={() => { stickToBottom.current = true; void sendMessage(turn.question, turn.id); }} />)}</div>}
          </div>
          {showScrollButton && <button type="button" onClick={() => { stickToBottom.current = true; scrollArea.current?.scrollTo({ top: scrollArea.current.scrollHeight }); setShowScrollButton(false); }} className="absolute bottom-3 left-1/2 flex -translate-x-1/2 items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600 shadow-sm"><ArrowDown className="h-3.5 w-3.5" />Latest message</button>}
        </div>
        <div className="border-t border-slate-100 bg-white p-3 sm:p-5">
          {turns.length > 0 && <div className="mb-3 flex gap-2 overflow-x-auto pb-1">{suggestions.slice(1, 3).map((prompt) => <button type="button" key={prompt} disabled={isStreaming} onClick={() => choosePrompt(prompt)} className="shrink-0 rounded-lg border border-slate-200 px-3 py-2 text-[11px] text-slate-500 hover:border-emerald/40 hover:text-emerald disabled:cursor-not-allowed disabled:opacity-50">{prompt}</button>)}</div>}
          <form onSubmit={submit} className="flex items-end gap-3 rounded-xl border border-slate-200 bg-slate-50/50 p-2.5 transition focus-within:border-emerald focus-within:ring-2 focus-within:ring-emerald/10">
            <label htmlFor="chat-question" className="sr-only">Your procurement question</label>
            <textarea ref={composer} id="chat-question" value={input} maxLength={4000} rows={2} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); event.currentTarget.form?.requestSubmit(); }
            }} placeholder={turns.length ? 'Ask a follow-up question…' : 'Ask anything about procurement data…'} className="max-h-32 min-h-12 flex-1 resize-none bg-transparent px-1 py-1 text-sm leading-6 text-slate-800 outline-none placeholder:text-slate-400" aria-describedby="chat-composer-hint" />
            <button type="submit" disabled={!input.trim() || isStreaming} aria-label={isStreaming ? 'Response in progress' : 'Send question'} className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-40">{isStreaming ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}</button>
          </form>
          <div id="chat-composer-hint" className="mt-2 flex flex-wrap justify-between gap-1 px-1 text-[10px] text-slate-400"><span>{isStreaming ? 'Working on your question. You can draft your next message.' : 'Enter to send · Shift + Enter for a new line'}</span><span>{input.length.toLocaleString()} / 4,000</span></div>
        </div>
      </section>
      <p className="mt-3 text-center text-[10px] text-slate-400">AI responses may contain errors. Verify important insights against the source data.</p>
    </div>
  );
}
