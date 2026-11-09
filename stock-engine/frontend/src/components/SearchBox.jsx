import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';

/**
 * Stock/ETF search with keyboard navigation.
 * variant "dark" is the existing top-bar style; variant "cream" is the
 * glassy-sidebar style (pale inset field, dark text, orange focus ring).
 */
export default function SearchBox({ variant = 'dark', inputRef: externalRef, onNavigate }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const navigate = useNavigate();
  const boxRef = useRef(null);
  const innerRef = useRef(null);
  const inputRef = externalRef || innerRef;

  useEffect(() => {
    if (query.trim().length < 1) {
      setResults([]);
      return;
    }
    const t = setTimeout(() => {
      api
        .search(query)
        .then((d) => {
          setResults(d.results);
          setOpen(true);
          setActive(0);
        })
        .catch(() => {});
    }, 180);
    return () => clearTimeout(t);
  }, [query]);

  useEffect(() => {
    const onClick = (e) => {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  const go = (symbol) => {
    setOpen(false);
    setQuery('');
    if (onNavigate) onNavigate();
    navigate(`/stock/${symbol}`);
  };

  const onKeyDown = (e) => {
    if (!open || results.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActive((a) => Math.min(a + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive((a) => Math.max(a - 1, 0));
    } else if (e.key === 'Enter') {
      go(results[active].symbol);
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  };

  const cream = variant === 'cream';

  return (
    <div ref={boxRef} className="relative w-full">
      <svg
        className={`pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 ${
          cream ? 'text-[#a39a8c]' : 'text-slate-500'
        }`}
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-4.35-4.35M17 10.5a6.5 6.5 0 1 1-13 0 6.5 6.5 0 0 1 13 0Z" />
      </svg>
      <input
        ref={inputRef}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => results.length && setOpen(true)}
        onKeyDown={onKeyDown}
        placeholder="Search stocks & ETFs"
        className={`w-full rounded-xl py-2 pl-9 text-sm outline-none transition ${
          cream
            ? 'border border-[rgba(120,90,40,0.14)] bg-[rgba(120,90,40,0.07)] pr-12 text-[#2b2118] placeholder-[#a39a8c] focus:border-[#e8622c]/60 focus:ring-2 focus:ring-[#e8622c]/25'
            : 'border border-white/10 bg-white/[0.06] pr-3 text-slate-200 placeholder-slate-500 backdrop-blur-xl focus:border-brand-400/60 focus:ring-2 focus:ring-brand-500/25'
        }`}
      />
      {cream && (
        <kbd className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 rounded-md border border-[rgba(120,90,40,0.16)] bg-white/70 px-1.5 py-0.5 text-[10px] font-semibold text-[#8a7f72]">
          ⌘K
        </kbd>
      )}
      {open && results.length > 0 && (
        <ul
          className={`absolute z-50 mt-2 max-h-72 w-full overflow-y-auto rounded-xl border shadow-xl backdrop-blur-xl ${
            cream
              ? 'border-white/70 bg-[#fffdf8]/95 shadow-[0_16px_40px_-16px_rgba(43,33,24,0.45)]'
              : 'border-white/10 bg-ink-900/90 shadow-card'
          }`}
        >
          {results.map((r, i) => (
            <li key={r.symbol}>
              <button
                onMouseEnter={() => setActive(i)}
                onClick={() => go(r.symbol)}
                className={`flex w-full items-center justify-between px-4 py-2.5 text-left text-sm ${
                  cream
                    ? i === active
                      ? 'bg-[rgba(120,90,40,0.08)]'
                      : ''
                    : i === active
                      ? 'bg-ink-700'
                      : ''
                }`}
              >
                <span>
                  <span className={`font-semibold ${cream ? 'text-[#2b2118]' : 'text-slate-100'}`}>
                    {r.symbol}
                  </span>
                  <span className={`ml-2 ${cream ? 'text-[#8a7f72]' : 'text-slate-400'}`}>{r.name}</span>
                </span>
                <span
                  className={`text-[10px] uppercase tracking-wide ${
                    cream ? 'text-[#a39a8c]' : 'text-slate-500'
                  }`}
                >
                  {r.type === 'etf' ? 'ETF' : r.sector}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
