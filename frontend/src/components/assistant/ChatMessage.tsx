import { lazy, Suspense, useState } from 'react';
import {
  AlertCircle,
  BadgeCheck,
  CalendarDays,
  Check,
  ChevronDown,
  Clipboard,
  Code2,
  Copy,
  Database,
  Loader2,
  RotateCcw,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  WandSparkles,
} from 'lucide-react';
import type { ChatTurn, Pipeline } from '../../types/chat';
import { Visualization } from './Visualization';
import { reportPdfDownloadUrl } from '../../services/reportService';

const MarkdownAnswer = lazy(() => import('./MarkdownAnswer'));

const formatTime = (value: string) => new Date(value).toLocaleTimeString([], {
  hour: 'numeric',
  minute: '2-digit',
});

const VISUALIZATION_REQUEST = /\b(?:chart|graph|plot|visuali[sz](?:e|ation)|metric card|kpi)\b/i;

function pipelineYear(pipeline: Pipeline | null): string | undefined {
  for (const stage of pipeline ?? []) {
    const match = stage.$match;
    if (match && typeof match === 'object' && !Array.isArray(match)) {
      const year = (match as Record<string, unknown>).year;
      if (typeof year === 'string' || typeof year === 'number') return String(year);
    }
  }
  return undefined;
}

function QueryPanel({ turn, verified }: { turn: ChatTurn; verified: boolean }) {
  const [expanded, setExpanded] = useState(turn.status !== 'streaming');
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied' | 'failed'>('idle');
  const query = JSON.stringify(turn.pipeline, null, 2);
  const year = pipelineYear(turn.pipeline);

  async function copyQuery() {
    try {
      await navigator.clipboard.writeText(query);
      setCopyStatus('copied');
    } catch {
      setCopyStatus('failed');
    }
  }

  return (
    <div className="mt-6 overflow-hidden rounded-xl border border-slate-200">
      <button type="button" onClick={() => setExpanded(!expanded)} aria-expanded={expanded} aria-controls={`query-${turn.id}`} className="flex w-full items-center gap-3 px-4 py-4 text-left">
        <WandSparkles className="h-[18px] w-[18px] shrink-0 text-slate-700" />
        <span className="min-w-0 flex-1">
          <span className="block text-sm font-semibold text-slate-900">How this answer was generated</span>
          <span className="mt-1 block text-xs leading-5 text-slate-500">{turn.queryDescription || 'Generated a MongoDB aggregation pipeline from your question.'}</span>
        </span>
        <ChevronDown className={`h-4 w-4 shrink-0 text-slate-700 transition-transform ${expanded ? 'rotate-180' : ''}`} />
      </button>

      <div id={`query-${turn.id}`} hidden={!expanded}>
        <div className="mx-4 mb-4 overflow-hidden rounded-lg border border-slate-200 bg-[#fbfcfe]">
          <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50/80 px-4 py-2.5">
            <span className="text-[11px] font-medium text-slate-500">MongoDB aggregation pipeline</span>
            <button type="button" onClick={() => void copyQuery()} className="flex items-center gap-2 rounded px-1 py-1 text-xs text-slate-600 transition hover:text-blue" aria-label="Copy generated MongoDB pipeline">
              {copyStatus === 'copied' ? <Check className="h-4 w-4" /> : <Clipboard className="h-4 w-4" />}
              {copyStatus === 'copied' ? 'Copied' : 'Copy query'}
            </button>
          </div>
          <pre tabIndex={0} aria-label="Generated MongoDB aggregation pipeline" className="max-h-72 overflow-auto py-3 text-xs leading-6 text-slate-700">
            {query.split('\n').map((line, index) => (
              <span key={`${index}-${line}`} className="flex min-w-max px-4">
                <span aria-hidden="true" className="mr-5 w-5 select-none text-right text-slate-400">{index + 1}</span>
                <code className="whitespace-pre">{line}</code>
              </span>
            ))}
          </pre>
        </div>
        {copyStatus === 'failed' && <p role="status" className="mx-4 mb-3 text-xs text-amber-700">Could not copy. You can select the query above.</p>}

        <div className="border-t border-slate-200 px-4 py-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
            <Database className="h-[18px] w-[18px]" />Sources &amp; metadata
          </div>
          <div className="mt-3 flex flex-wrap gap-3">
            <span className="inline-flex items-center gap-2 rounded-xl bg-emerald-50 px-3.5 py-2 text-xs font-medium text-emerald-700">
              <Database className="h-4 w-4" />Dataset: CA Public Procurement
            </span>
            {year && (
              <span className="inline-flex items-center gap-2 rounded-xl bg-blue-50 px-3.5 py-2 text-xs font-medium text-blue-700">
                <CalendarDays className="h-4 w-4" />Year: {year}
              </span>
            )}
            <span className="inline-flex items-center gap-2 rounded-xl bg-violet-50 px-3.5 py-2 text-xs font-medium text-violet-700">
              <Code2 className="h-4 w-4" />Aggregation pipeline
            </span>
            {verified && (
              <span className="inline-flex items-center gap-2 rounded-xl bg-emerald-50 px-3.5 py-2 text-xs font-medium text-emerald-700">
                <BadgeCheck className="h-4 w-4" />Verified from source data
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export function ChatMessage({ turn, onRetry, canRetry }: {
  turn: ChatTurn;
  onRetry: () => void;
  canRetry: boolean;
}) {
  const [answerCopied, setAnswerCopied] = useState(false);
  const [feedback, setFeedback] = useState<'up' | 'down'>();
  const streaming = turn.status === 'streaming';
  const running = turn.progress.find((item) => item.status === 'running');
  const queryVerified = turn.progress.length === 0
    || turn.progress.some((item) => item.step === 'execute_query' && item.status === 'complete');
  const hasVisualizationOutput = Boolean(turn.visualization)
    || turn.progress.some((item) => item.step === 'generate_visualization')
    || VISUALIZATION_REQUEST.test(turn.question);

  async function copyAnswer() {
    try {
      await navigator.clipboard.writeText(turn.answer);
      setAnswerCopied(true);
    } catch {
      setAnswerCopied(false);
    }
  }

  return (
    <article className="space-y-5" aria-label="Conversation turn">
      <div className="ml-auto flex max-w-[620px] items-start justify-end gap-3">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#1765a3] text-[11px] font-semibold text-white">AA</span>
        <div className="min-w-0">
          <div className="rounded-xl rounded-tl-sm bg-blue-100 px-5 py-3.5">
            <p className="whitespace-pre-wrap break-words text-sm leading-6 text-slate-900">{turn.question}</p>
          </div>
          <time dateTime={turn.createdAt} className="mt-1.5 block text-right text-[10px] text-slate-500">{formatTime(turn.createdAt)}</time>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-card sm:p-5">
        <div className="flex items-start gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald">
            <Sparkles className="h-5 w-5" />
          </span>
          <div className="flex min-w-0 flex-1 items-center gap-3 pt-2">
            <h3 className="text-xs font-bold text-slate-900">Procurement Assistant</h3>
            <time dateTime={turn.createdAt} className="text-[10px] text-slate-500">{formatTime(turn.createdAt)}</time>
            {streaming && <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald">Working</span>}
          </div>
          {turn.answer && !streaming && (
            <div className="flex items-center text-slate-500">
              <button type="button" onClick={() => void copyAnswer()} className="rounded-md p-2 transition hover:bg-slate-100 hover:text-slate-800" aria-label="Copy answer">
                {answerCopied ? <Check className="h-[17px] w-[17px]" /> : <Copy className="h-[17px] w-[17px]" />}
              </button>
              <button type="button" onClick={() => setFeedback(feedback === 'up' ? undefined : 'up')} aria-pressed={feedback === 'up'} className={`rounded-md p-2 transition hover:bg-slate-100 ${feedback === 'up' ? 'text-blue' : 'hover:text-slate-800'}`} aria-label="Helpful answer"><ThumbsUp className="h-[17px] w-[17px]" /></button>
              <button type="button" onClick={() => setFeedback(feedback === 'down' ? undefined : 'down')} aria-pressed={feedback === 'down'} className={`rounded-md p-2 transition hover:bg-slate-100 ${feedback === 'down' ? 'text-blue' : 'hover:text-slate-800'}`} aria-label="Unhelpful answer"><ThumbsDown className="h-[17px] w-[17px]" /></button>
            </div>
          )}
        </div>

        <div className="mt-1 sm:pl-14">
          {streaming && turn.progress.length > 0 && !turn.answer && (
            <div className="mb-4 flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-2.5 text-xs text-slate-600" role="status">
              <Loader2 className="h-4 w-4 animate-spin text-emerald" />{running?.label ?? 'Preparing response'}…
            </div>
          )}
          {turn.answer && (
            <Suspense fallback={<p className="text-sm text-slate-500">Formatting response…</p>}>
              <MarkdownAnswer
                text={turn.answer}
                suppressVisualCode={hasVisualizationOutput}
              />
            </Suspense>
          )}
          {turn.visualization && <Visualization visualization={turn.visualization} />}
          {turn.report && <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-4"><p className="text-sm font-semibold text-slate-900">{turn.report.title}</p><p className="mt-1 text-xs text-slate-600">{turn.report.period} · {turn.report.status}</p><div className="mt-3 flex gap-3 text-xs font-semibold text-emerald-800"><a href={`/reports?open=${encodeURIComponent(turn.report.id)}`}>Open preview</a><a href={reportPdfDownloadUrl(turn.report.id)}>Download PDF</a></div></div>}
          {turn.pipeline !== null && <QueryPanel key={`${turn.queryGeneratedAt}-${streaming}`} turn={turn} verified={queryVerified} />}
          {turn.error && (
            <div role="alert" className="mt-4 rounded-lg border border-rose-100 bg-rose-50 p-3 text-sm text-rose-700">
              <p className="flex items-start gap-2"><AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />{turn.error}</p>
              {canRetry && <button type="button" onClick={onRetry} className="mt-2 flex items-center gap-1.5 text-xs font-semibold hover:underline"><RotateCcw className="h-3.5 w-3.5" />Try again</button>}
            </div>
          )}
        </div>
      </div>
    </article>
  );
}
