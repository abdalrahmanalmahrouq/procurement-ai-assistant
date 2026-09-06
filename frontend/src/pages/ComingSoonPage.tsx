import { ArrowLeft, Blocks } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';

export function ComingSoonPage() {
  const { section = 'page' } = useParams();
  const title = section.replace(/-/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
  return <div className="card mx-auto flex min-h-[540px] max-w-3xl flex-col items-center justify-center p-8 text-center"><span className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-50 text-blue"><Blocks className="h-8 w-8" /></span><h2 className="mt-5 text-2xl font-bold">{title}</h2><p className="mt-2 max-w-md text-sm leading-6 text-slate-500">The shared navigation and page shell are ready. This section can be connected when its backend endpoint and requirements are available.</p><Link to="/" className="primary-button mt-6"><ArrowLeft className="h-4 w-4" />Back to overview</Link></div>;
}
