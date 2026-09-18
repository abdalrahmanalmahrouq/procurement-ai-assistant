import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const VISUALIZATION_FENCE = /```(?:mermaid|text)?[^\n]*\n?[\s\S]*?(?:```|$)/gi;
const MERMAID_FENCE = /```mermaid[^\n]*\n?[\s\S]*?(?:```|$)/gi;

function displayAnswer(text: string, suppressVisualCode: boolean): string {
  return text
    .replace(suppressVisualCode ? VISUALIZATION_FENCE : MERMAID_FENCE, '')
    .trim();
}

export default function MarkdownAnswer({ text, suppressVisualCode }: {
  text: string;
  suppressVisualCode: boolean;
}) {
  const content = displayAnswer(text, suppressVisualCode);
  if (!content) return null;

  return (
    <div className="break-words text-[15px] leading-7 text-slate-700">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => <h1 className="mb-3 mt-5 text-xl font-bold text-slate-950 first:mt-0">{children}</h1>,
          h2: ({ children }) => <h2 className="mb-2 mt-5 text-lg font-bold text-slate-950 first:mt-0">{children}</h2>,
          h3: ({ children }) => <h3 className="mb-2 mt-4 text-base font-semibold text-slate-950 first:mt-0">{children}</h3>,
          p: ({ children }) => <p className="mb-3 whitespace-pre-wrap last:mb-0">{children}</p>,
          strong: ({ children }) => <strong className="font-semibold text-slate-950">{children}</strong>,
          ul: ({ children }) => <ul className="mb-3 list-disc space-y-1 pl-6 last:mb-0">{children}</ul>,
          ol: ({ children }) => <ol className="mb-3 list-decimal space-y-1 pl-6 last:mb-0">{children}</ol>,
          li: ({ children }) => <li className="pl-1">{children}</li>,
          blockquote: ({ children }) => <blockquote className="my-3 border-l-4 border-slate-300 pl-4 text-slate-600">{children}</blockquote>,
          a: ({ children, href }) => <a href={href} target="_blank" rel="noreferrer" className="font-medium text-blue underline underline-offset-2">{children}</a>,
          code: ({ children, className }) => <code className={`${className ?? ''} rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[13px] text-slate-800`}>{children}</code>,
          pre: ({ children }) => <pre className="my-3 overflow-x-auto rounded-lg bg-slate-950 p-4 text-sm leading-6 text-slate-100 [&_code]:bg-transparent [&_code]:p-0 [&_code]:text-inherit">{children}</pre>,
          table: ({ children }) => <div className="my-4 overflow-x-auto rounded-lg border border-slate-200"><table className="min-w-full border-collapse text-left text-sm">{children}</table></div>,
          thead: ({ children }) => <thead className="bg-slate-50 text-slate-900">{children}</thead>,
          th: ({ children }) => <th className="border-b border-slate-200 px-3 py-2 font-semibold">{children}</th>,
          td: ({ children }) => <td className="border-b border-slate-100 px-3 py-2 align-top last:text-right">{children}</td>,
          hr: () => <hr className="my-5 border-slate-200" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
