import type { ReactNode } from 'react';
import { Info } from 'lucide-react';

interface CardProps {
  title?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  padded?: boolean;
  info?: boolean;
}

export function Card({ title, action, children, className = '', padded = true, info = false }: CardProps) {
  return (
    <section className={`card ${padded ? 'p-4' : ''} ${className}`}>
      {(title || action) && (
        <div className={`flex items-center justify-between gap-3 ${padded ? 'mb-4' : 'border-b border-slate-100 px-4 py-3'}`}>
          {title && (
            <div className="flex items-center gap-2">
              <h2 className="section-title">{title}</h2>
              {info && <Info className="h-3.5 w-3.5 text-slate-400" />}
            </div>
          )}
          {action}
        </div>
      )}
      {children}
    </section>
  );
}
