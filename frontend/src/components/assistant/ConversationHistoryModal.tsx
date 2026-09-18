import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Loader2, MessageSquare, Search, Trash2, X } from 'lucide-react';
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
  deletingConversationId?: string;
  error?: string;
  onClose: () => void;
  onOpenConversation: (id: string) => void;
  onDeleteConversation: (id: string) => Promise<boolean>;
}

export function ConversationHistoryModal({
  open,
  conversations,
  activeConversationId,
  loading,
  deletingConversationId,
  error,
  onClose,
  onOpenConversation,
  onDeleteConversation,
}: ConversationHistoryModalProps) {
  const [search, setSearch] = useState('');
  const [conversationToDelete, setConversationToDelete] = useState<ConversationSummary>();
  const filteredConversations = useMemo(() => {
    const query = search.trim().toLocaleLowerCase();
    return query
      ? conversations.filter((conversation) => conversation.title.toLocaleLowerCase().includes(query))
      : conversations;
  }, [conversations, search]);

  useEffect(() => {
    if (!open) return;
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key !== 'Escape' || deletingConversationId) return;
      if (conversationToDelete) setConversationToDelete(undefined);
      else onClose();
    }
    document.addEventListener('keydown', closeOnEscape);
    return () => document.removeEventListener('keydown', closeOnEscape);
  }, [conversationToDelete, deletingConversationId, onClose, open]);

  function closeHistory() {
    if (deletingConversationId) return;
    setConversationToDelete(undefined);
    onClose();
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/45 p-4 backdrop-blur-[1px]" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) closeHistory(); }}>
      <section role="dialog" aria-modal="true" aria-labelledby="chat-history-title" className="w-full max-w-[720px] rounded-xl bg-white p-6 shadow-2xl sm:p-7">
        <div className="flex items-center justify-between">
          <h2 id="chat-history-title" className="text-xl font-bold tracking-[-0.02em] text-slate-950">Chat history</h2>
          <button type="button" onClick={closeHistory} className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-800" aria-label="Close chat history">
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
            <div
              key={conversation.id}
              className={`flex min-h-12 w-full items-center rounded-lg border transition ${activeConversationId === conversation.id ? 'border-blue-200 bg-blue-50/60' : 'border-slate-200 hover:border-blue-200 hover:bg-slate-50'}`}
            >
              <button
                type="button"
                disabled={loading || Boolean(deletingConversationId)}
                onClick={() => onOpenConversation(conversation.id)}
                aria-current={activeConversationId === conversation.id ? 'page' : undefined}
                className="flex min-w-0 flex-1 items-center gap-4 px-4 py-3 text-left disabled:cursor-wait disabled:opacity-60"
              >
                <MessageSquare className="h-[18px] w-[18px] shrink-0 text-slate-600" />
                <span className="min-w-0 flex-1 truncate text-sm font-medium text-slate-900">{conversation.title}</span>
                <time dateTime={conversation.updated_at} className="shrink-0 text-xs text-slate-500">{formatDate(conversation.updated_at)}</time>
              </button>
              <button
                type="button"
                disabled={loading || Boolean(deletingConversationId)}
                onClick={() => setConversationToDelete(conversation)}
                className="mr-2 flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-slate-400 transition hover:bg-rose-50 hover:text-rose-600 disabled:cursor-wait disabled:opacity-50"
                aria-label={`Delete ${conversation.title}`}
                title="Delete conversation"
              >
                {deletingConversationId === conversation.id
                  ? <Loader2 className="h-4 w-4 animate-spin" />
                  : <Trash2 className="h-4 w-4" />}
              </button>
            </div>
          ))}
        </div>
      </section>

      {conversationToDelete && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/35 p-4"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget && !deletingConversationId) {
              setConversationToDelete(undefined);
            }
          }}
        >
          <section
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="delete-conversation-title"
            aria-describedby="delete-conversation-description"
            className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl"
          >
            <div className="flex items-start gap-4">
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-rose-50 text-rose-600">
                <AlertTriangle className="h-5 w-5" />
              </span>
              <div className="min-w-0 flex-1">
                <h3 id="delete-conversation-title" className="text-lg font-bold text-slate-950">Delete conversation?</h3>
                <p id="delete-conversation-description" className="mt-2 text-sm leading-6 text-slate-600">
                  This will remove <strong className="font-semibold text-slate-800">“{conversationToDelete.title}”</strong> from your chat history.
                </p>
              </div>
            </div>

            {error && <p role="alert" className="mt-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}

            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                autoFocus
                disabled={Boolean(deletingConversationId)}
                onClick={() => setConversationToDelete(undefined)}
                className="h-10 rounded-lg border border-slate-200 px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-wait disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={Boolean(deletingConversationId)}
                onClick={async () => {
                  const deleted = await onDeleteConversation(conversationToDelete.id);
                  if (deleted) setConversationToDelete(undefined);
                }}
                className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-rose-600 px-4 text-sm font-semibold text-white transition hover:bg-rose-700 disabled:cursor-wait disabled:opacity-60"
              >
                {deletingConversationId === conversationToDelete.id ? (
                  <><Loader2 className="h-4 w-4 animate-spin" />Deleting…</>
                ) : (
                  <><Trash2 className="h-4 w-4" />Delete</>
                )}
              </button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
