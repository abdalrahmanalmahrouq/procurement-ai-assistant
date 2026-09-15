import { useState } from 'react';
import { AlertCircle, BarChart3, Check, CheckCircle2, ChevronDown, Clipboard, Code2, Database, Loader2, RotateCcw, UserRound } from 'lucide-react';
import type { ChatTurn } from '../../types/chat';

const formatTime = (value: string) => new Date(value).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });

function AnswerText({ text }: { text: string }) {
  // Render basic emphasis as React text, never interpreting model output as HTML.
  return <div className="whitespace-pre-wrap break-words text-sm leading-7 text-slate-700">{
    text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).map((part, index) =>
      part.startsWith('**') && part.endsWith('**') ? <strong key={index} className="font-semibold text-slate-900">{part.slice(2, -2)}</strong>
        : part.startsWith('`') && part.endsWith('`') ? <code key={index} className="rounded bg-slate-100 px-1 text-xs">{part.slice(1, -1)}</code> : part,
    )
  }</div>;
}

function QueryPanel({ turn }: { turn: ChatTurn }) {
  const [expanded, setExpanded] = useState(turn.status !== 'streaming');
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied' | 'failed'>('idle');
  async function copyQuery() {
    try {
      await navigator.clipboard.writeText(JSON.stringify(turn.pipeline, null, 2));
      setCopyStatus('copied');
    } catch { setCopyStatus('failed'); }
  }
  return (
    <div className="mt-4 overflow-hidden rounded-xl border border-slate-200">
      <div className="flex flex-wrap items-center justify-between gap-2 bg-slate-50 px-4 py-3">
        <button type="button" onClick={() => setExpanded(!expanded)} aria-expanded={expanded} aria-controls={`query-${turn.id}`} className="flex items-center gap-2 text-left text-xs font-semibold text-slate-700">
          <Code2 className="h-4 w-4 shrink-0 text-emerald" />Generated MongoDB pipeline
          <ChevronDown className={`h-3.5 w-3.5 shrink-0 transition-transform ${expanded ? 'rotate-180' : ''}`} />
        </button>
        <button type="button" onClick={() => void copyQuery()} className="flex items-center gap-1.5 rounded px-1 py-1 text-xs text-slate-500 hover:text-emerald" aria-label="Copy generated MongoDB pipeline">
          {copyStatus === 'copied' ? <Check className="h-3.5 w-3.5" /> : <Clipboard className="h-3.5 w-3.5" />}{copyStatus === 'copied' ? 'Copied' : 'Copy'}
        </button>
      </div>
      <div id={`query-${turn.id}`} hidden={!expanded}>
        {turn.queryDescription && <p className="border-t border-slate-200 px-4 py-3 text-xs leading-5 text-slate-500">{turn.queryDescription}</p>}
        <pre tabIndex={0} aria-label="Generated MongoDB aggregation pipeline" className="max-h-80 overflow-auto border-t border-slate-100 bg-white p-4 text-[11px] leading-6 text-slate-700"><code>{JSON.stringify(turn.pipeline, null, 2)}</code></pre>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 px-4 py-2.5 text-[10px] text-slate-500">
        <span>{turn.queryGeneratedAt ? `Generated at ${formatTime(turn.queryGeneratedAt)}` : 'Generated query'}{turn.retryCount > 0 ? ` · ${turn.retryCount} correction${turn.retryCount === 1 ? '' : 's'}` : ''}</span>
        <button type="button" onClick={() => setExpanded(!expanded)} className="font-medium text-emerald">{expanded ? 'Show less' : 'Show query'}</button>
      </div>
      {copyStatus === 'failed' && <p role="status" className="px-4 pb-3 text-xs text-amber-700">Could not copy. You can select and copy the query above.</p>}
      {copyStatus === 'copied' && <span role="status" className="sr-only">Query copied to clipboard.</span>}
    </div>
  );
}

export function ChatMessage({ turn, onRetry, canRetry }: { turn: ChatTurn; onRetry: () => void; canRetry: boolean }) {
  const streaming = turn.status === 'streaming';
  const running = turn.progress.find((item) => item.status === 'running');
  const querySucceeded = turn.progress.some((item) => item.step === 'execute_query' && item.status === 'complete');
  const hasWarning = turn.progress.some((item) => item.status === 'error');
  return (
    <article className="space-y-6" aria-label="Conversation turn">
      <div className="ml-auto flex max-w-[92%] items-start justify-end gap-3 sm:max-w-[85%]">
        <div className="min-w-0 rounded-2xl rounded-tr-sm bg-emerald-50 px-4 py-3">
          <p className="whitespace-pre-wrap break-words text-sm leading-6 text-slate-800">{turn.question}</p>
          <time dateTime={turn.createdAt} className="mt-1 block text-right text-[10px] text-slate-500">{formatTime(turn.createdAt)}</time>
        </div>
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-50 text-emerald"><UserRound className="h-4 w-4" /></span>
      </div>
      <div className="flex items-start gap-2 sm:gap-3">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-50 text-emerald"><BarChart3 className="h-4 w-4" /></span>
        <div className="min-w-0 flex-1 rounded-2xl rounded-tl-sm border border-slate-200 bg-white p-4 sm:p-5">
          <div className="mb-3 flex items-center gap-2 text-xs font-semibold text-slate-800">Procurement Assistant{streaming && <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald">Working</span>}</div>
          {turn.progress.length > 0 && <details open={streaming} className="mb-4 rounded-lg bg-slate-50 px-3 py-2.5">
            <summary className="cursor-pointer text-xs text-slate-600"><span role="status">{streaming ? running?.label ?? 'Finishing response' : turn.status === 'error' ? 'Response interrupted' : hasWarning ? 'Process completed with an issue' : 'Response complete'}</span></summary>
            <ol className="mt-3 space-y-2.5 border-t border-slate-200 pt-3">
              {turn.progress.map((item) => <li key={item.step} className="flex items-center gap-2 text-xs text-slate-600">
                {item.status === 'running' && streaming ? <Loader2 className="h-3.5 w-3.5 animate-spin text-emerald" /> : item.status === 'error' || item.status === 'running' ? <AlertCircle className="h-3.5 w-3.5 text-amber-600" /> : <CheckCircle2 className="h-3.5 w-3.5 text-emerald" />}
                <span>{item.status === 'running' && !streaming ? `${item.label} — interrupted` : item.label}</span>
              </li>)}
            </ol>
          </details>}
          {turn.answer ? <AnswerText text={turn.answer} /> : streaming && <div className="flex items-center gap-2 text-sm text-slate-500"><Loader2 className="h-4 w-4 animate-spin text-emerald" />{running?.label ?? 'Connecting to the assistant'}…</div>}
          {turn.status === 'complete' && querySucceeded && <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-slate-500"><span className="flex items-center gap-1.5"><Database className="h-3.5 w-3.5" />Source: procurement database</span><span>{turn.resultCount?.toLocaleString()} query result{turn.resultCount === 1 ? '' : 's'} returned</span></div>}
          {turn.pipeline !== null && <QueryPanel key={`${turn.queryGeneratedAt}-${streaming}`} turn={turn} />}
          {turn.error && <div role="alert" className="mt-4 rounded-lg border border-rose-100 bg-rose-50 p-3 text-sm text-rose-700"><p>{turn.error}</p>{canRetry && <button type="button" onClick={onRetry} className="mt-2 flex items-center gap-1.5 text-xs font-semibold hover:underline"><RotateCcw className="h-3.5 w-3.5" />Try again</button>}</div>}
        </div>
      </div>
    </article>
  );
}
