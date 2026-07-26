import { useEffect, useRef, useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { api } from '../api';

function Logo() {
  return (
    <NavLink to="/" className="flex items-center gap-2.5 shrink-0">
      <svg viewBox="0 0 32 32" className="h-8 w-8">
        <rect width="32" height="32" rx="8" className="fill-ink-700" />
        <path
          d="M6 22 L13 14 L18 18 L26 8"
          className="stroke-bull"
          strokeWidth="3"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span className="text-lg font-extrabold tracking-tight text-white">
        Trend<span className="text-brand-400">Wise</span>
      </span>
    </NavLink>
  );
}

function SearchBox() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const navigate = useNavigate();
  const boxRef = useRef(null);

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

  return (
    <div ref={boxRef} className="relative w-full max-w-md">
      <svg
        className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-4.35-4.35M17 10.5a6.5 6.5 0 1 1-13 0 6.5 6.5 0 0 1 13 0Z" />
      </svg>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => results.length && setOpen(true)}
        onKeyDown={onKeyDown}
        placeholder="Search stocks & ETFs — e.g. RELIANCE, Gold BeES"
        className="w-full rounded-xl border border-ink-600 bg-ink-800 py-2 pl-9 pr-3 text-sm text-slate-200 placeholder-slate-500 outline-none transition focus:border-brand-500/60 focus:ring-2 focus:ring-brand-500/20"
      />
      {open && results.length > 0 && (
        <ul className="absolute z-30 mt-2 w-full overflow-hidden rounded-xl border border-ink-600 bg-ink-800 shadow-card">
          {results.map((r, i) => (
            <li key={r.symbol}>
              <button
                onMouseEnter={() => setActive(i)}
                onClick={() => go(r.symbol)}
                className={`flex w-full items-center justify-between px-4 py-2.5 text-left text-sm ${
                  i === active ? 'bg-ink-700' : ''
                }`}
              >
                <span>
                  <span className="font-semibold text-slate-100">{r.symbol}</span>
                  <span className="ml-2 text-slate-400">{r.name}</span>
                </span>
                <span className="text-[10px] uppercase tracking-wide text-slate-500">
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

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/screener', label: 'Screener' },
  { to: '/etfs', label: 'ETFs' },
  { to: '/watchlist', label: 'Watchlist' },
];

export default function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-ink-700 bg-ink-900/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center gap-6 px-4 py-3 sm:px-6">
        <Logo />
        <nav className="hidden items-center gap-1 md:flex">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              className={({ isActive }) => `btn-pill ${isActive ? 'btn-pill-active' : ''}`}
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
        <div className="ml-auto flex-1 md:max-w-md">
          <SearchBox />
        </div>
      </div>
      <nav className="flex items-center gap-1 overflow-x-auto px-4 pb-2 md:hidden">
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.to === '/'}
            className={({ isActive }) => `btn-pill whitespace-nowrap ${isActive ? 'btn-pill-active' : ''}`}
          >
            {l.label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}
