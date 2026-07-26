import { Link } from 'react-router-dom';
import { fmt, verdictColor } from '../api';

export function VerdictBadge({ verdict, className = '' }) {
  if (!verdict) return null;
  return <span className={`chip ${verdictColor(verdict)} ${className}`}>{verdict}</span>;
}

export function ChangePct({ value, className = '' }) {
  if (value == null) return <span className="text-slate-500">—</span>;
  const up = value >= 0;
  return (
    <span className={`num font-semibold ${up ? 'text-bull' : 'text-bear'} ${className}`}>
      {up ? '▲' : '▼'} {fmt.pct(Math.abs(value)).replace('+', '')}
    </span>
  );
}

export function SentimentChip({ label }) {
  const styles = {
    positive: 'text-bull bg-bull/10',
    negative: 'text-bear bg-bear/10',
    neutral: 'text-slate-400 bg-ink-700',
  };
  return <span className={`chip ${styles[label] || styles.neutral}`}>{label}</span>;
}

export function SectionTitle({ children, right }) {
  return (
    <div className="mb-3 flex items-center justify-between">
      <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">{children}</h2>
      {right}
    </div>
  );
}

export function SymbolLink({ symbol, name, className = '' }) {
  return (
    <Link to={`/stock/${symbol}`} className={`group ${className}`}>
      <span className="font-semibold text-slate-100 group-hover:text-brand-400 transition-colors">{symbol}</span>
      {name && <span className="ml-2 hidden text-xs text-slate-500 sm:inline">{name}</span>}
    </Link>
  );
}

export function Skeleton({ className = '' }) {
  return <div className={`skeleton ${className}`} />;
}

export function ErrorNote({ error, retry }) {
  return (
    <div className="card-pad text-center">
      <p className="text-sm text-slate-400">{String(error?.message || error || 'Something went wrong.')}</p>
      {retry && (
        <button onClick={retry} className="mt-3 rounded-lg bg-ink-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-ink-500">
          Retry
        </button>
      )}
    </div>
  );
}

export function DemoBanner({ source }) {
  if (source !== 'demo') return null;
  return (
    <div className="mb-4 rounded-xl border border-amber-400/25 bg-amber-400/10 px-4 py-2.5 text-xs text-amber-200">
      Live market feed is unreachable — showing deterministic <b>demo data</b> so you can explore the product. Set
      <code className="mx-1 rounded bg-ink-800 px-1.5 py-0.5">DEMO_MODE=off</code> in production.
    </div>
  );
}
