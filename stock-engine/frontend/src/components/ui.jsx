import { useEffect, useRef, useState } from 'react';
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
        <button onClick={retry} className="glass-btn mt-3">
          Retry
        </button>
      )}
    </div>
  );
}

/* Scroll-reveal wrapper: fades/slides content in the first time it scrolls
   into view. Pass delay (ms) for staggered entrances. */
export function Reveal({ children, delay = 0, className = '' }) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setVisible(true);
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setVisible(true);
          io.disconnect();
        }
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return (
    <div
      ref={ref}
      className={`reveal ${visible ? 'reveal-visible' : ''} ${className}`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </div>
  );
}

/* 3D tilt card: tilts toward the cursor with a moving light glare.
   Wrap a .card element with it; the card itself keeps its own styling. */
export function TiltCard({ children, max = 7, className = '' }) {
  const rootRef = useRef(null);
  const innerRef = useRef(null);
  const onMove = (e) => {
    const root = rootRef.current;
    const inner = innerRef.current;
    if (!root || !inner) return;
    const r = root.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width;
    const y = (e.clientY - r.top) / r.height;
    inner.style.transform = `rotateX(${((0.5 - y) * 2 * max).toFixed(2)}deg) rotateY(${((x - 0.5) * 2 * max).toFixed(2)}deg) translateZ(6px)`;
    inner.style.setProperty('--glare-x', `${x * 100}%`);
    inner.style.setProperty('--glare-y', `${y * 100}%`);
  };
  const onLeave = () => {
    if (innerRef.current) innerRef.current.style.transform = '';
  };
  return (
    <div ref={rootRef} onMouseMove={onMove} onMouseLeave={onLeave} className={`tilt ${className}`}>
      <div ref={innerRef} className="tilt-inner relative h-full">
        {children}
        <div className="tilt-glare" aria-hidden />
      </div>
    </div>
  );
}


