import { useEffect, useMemo, useState } from 'react';
import { MessageSquare, Search, X } from 'lucide-react';
import type { ConversationSummary } from '../../types/chat';

const formatDate = (value: string) => new Date(value).toLocaleDateString([], {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
});

interface ConversationHistoryModalProps {
  open: boolean;
  conversations: ConversationSummary[];
  activeConversationId?: string;
  loading: boolean;
  error?: string;
  onClose: () => void;
  onOpenConversation: (id: string) => void;
}

export function ConversationHistoryModal({
  open,
  conversations,
  activeConversationId,
  loading,
  error,
  onClose,
  onOpenConversation,
}: ConversationHistoryModalProps) {
  const [search, setSearch] = useState('');
  const filteredConversations = useMemo(() => {
    const query = search.trim().toLocaleLowerCase();
    return query
      ? conversations.filter((conversation) => conversation.title.toLocaleLowerCase().includes(query))
      : conversations;
  }, [conversations, search]);

  useEffect(() => {
    if (!open) return;
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose();
    }
    document.addEventListener('keydown', closeOnEscape);
    return () => document.removeEventListener('keydown', closeOnEscape);
  }, [onClose, open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/45 p-4 backdrop-blur-[1px]" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section role="dialog" aria-modal="true" aria-labelledby="chat-history-title" className="w-full max-w-[720px] rounded-xl bg-white p-6 shadow-2xl sm:p-7">
        <div className="flex items-center justify-between">
          <h2 id="chat-history-title" className="text-xl font-bold tracking-[-0.02em] text-slate-950">Chat history</h2>
          <button type="button" onClick={onClose} className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-800" aria-label="Close chat history">
            <X className="h-5 w-5" />
          </button>
        </div>

        <label className="mt-5 flex h-11 items-center gap-3 rounded-lg border border-slate-200 px-4 text-slate-500 transition focus-within:border-blue-300 focus-within:ring-2 focus-within:ring-blue-100">
          <Search className="h-5 w-5 shrink-0" />
          <span className="sr-only">Search conversations</span>
          <input value={search} onChange={(event) => setSearch(event.target.value)} autoFocus placeholder="Search conversations..." className="min-w-0 flex-1 bg-transparent text-sm text-slate-800 outline-none placeholder:text-slate-400" />
        </label>

        <div className="mt-3 max-h-[430px] space-y-1.5 overflow-y-auto">
          {error && <p role="alert" className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
          {!error && filteredConversations.length === 0 && (
            <p className="py-10 text-center text-sm text-slate-500">
              {search ? 'No conversations match your search.' : 'No saved conversations yet.'}
            </p>
          )}
          {filteredConversations.map((conversation) => (
            <button
              type="button"
              key={conversation.id}
              disabled={loading}
              onClick={() => onOpenConversation(conversation.id)}
              aria-current={activeConversationId === conversation.id ? 'page' : undefined}
              className={`flex min-h-12 w-full items-center gap-4 rounded-lg border px-4 py-3 text-left transition disabled:cursor-wait disabled:opacity-60 ${activeConversationId === conversation.id ? 'border-blue-200 bg-blue-50/60' : 'border-slate-200 hover:border-blue-200 hover:bg-slate-50'}`}
            >
              <MessageSquare className="h-[18px] w-[18px] shrink-0 text-slate-600" />
              <span className="min-w-0 flex-1 truncate text-sm font-medium text-slate-900">{conversation.title}</span>
              <time dateTime={conversation.updated_at} className="shrink-0 text-xs text-slate-500">{formatDate(conversation.updated_at)}</time>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
