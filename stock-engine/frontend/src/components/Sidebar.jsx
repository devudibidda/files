import { useEffect, useRef } from 'react';
import { NavLink } from 'react-router-dom';
import SearchBox from './SearchBox';

const ACCENT = '#e8622c';

const SECTIONS = [
  {
    heading: 'Explore',
    items: [
      {
        to: '/',
        label: 'Dashboard',
        tile: '#ea580c',
        icon: 'M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75',
      },
      {
        to: '/screener',
        label: 'Screener',
        tile: '#2563eb',
        icon: 'M12 3c2.755 0 5.455.232 8.083.678.533.09.917.556.917 1.096v1.044a2.25 2.25 0 01-.659 1.591l-5.432 5.432a2.25 2.25 0 00-.659 1.591v2.927a2.25 2.25 0 01-1.244 2.013L9.75 21v-6.568a2.25 2.25 0 00-.659-1.591L3.659 7.409A2.25 2.25 0 013 5.818V4.774c0-.54.384-1.006.917-1.096A48.32 48.32 0 0112 3z',
      },
      {
        to: '/calls',
        label: 'Calls',
        tile: '#16a34a',
        icon: 'M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z',
      },
    ],
  },
  {
    heading: 'Markets',
    items: [
      {
        to: '/etfs',
        label: 'ETFs',
        tile: '#7c3aed',
        icon: 'M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z',
      },
      {
        to: '/mutual-funds',
        label: 'Mutual Funds',
        tile: '#0d9488',
        icon: 'M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125',
      },
      {
        to: '/watchlist',
        label: 'Watchlist',
        tile: '#e11d48',
        icon: 'M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z',
      },
    ],
  },
];

function Tile({ color, icon, size = 'h-10 w-10' }) {
  return (
    <span
      className={`flex shrink-0 items-center justify-center rounded-xl text-white shadow-sm ${size}`}
      style={{ backgroundColor: color }}
    >
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
        <path strokeLinecap="round" strokeLinejoin="round" d={icon} />
      </svg>
    </span>
  );
}

function FadeLabel({ open, delay, children, className = '' }) {
  return (
    <span
      className={`whitespace-nowrap transition-all duration-300 ${open ? 'max-w-[190px] opacity-100' : 'max-w-0 opacity-0'} ${className}`}
      style={{ transitionDelay: open ? `${delay}ms` : '0ms' }}
    >
      {children}
    </span>
  );
}

export default function Sidebar({ open, onToggle }) {
  const searchRef = useRef(null);

  const focusSearch = () => {
    setTimeout(() => searchRef.current && searchRef.current.focus(), open ? 0 : 420);
  };

  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (!open) onToggle();
        focusSearch();
      }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onToggle]);

  let stagger = 0;
  const nextDelay = () => {
    stagger += 45;
    return stagger;
  };

  return (
    <aside className="fixed left-4 top-1/2 z-40 hidden -translate-y-1/2 md:block" aria-label="Main menu">
      <div
        className="glass-sidebar relative flex max-h-[calc(100vh-2rem)] flex-col p-2 transition-[width] duration-500 ease-[cubic-bezier(0.22,1,0.36,1)]"
        style={{ width: open ? 280 : 72 }}
      >
        {/* Header */}
        <div className={`flex items-center rounded-2xl px-1.5 py-1.5 ${open ? 'gap-3' : 'gap-0'}`}>
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#2b2118] shadow-sm">
            <svg viewBox="0 0 32 32" className="h-5 w-5">
              <path
                d="M6 22 L13 14 L18 18 L26 8"
                stroke="#ffffff"
                strokeWidth="3.5"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>
          <FadeLabel open={open} delay={nextDelay()}>
            <span className="flex flex-col leading-tight">
              <span className="font-display text-[17px] font-extrabold tracking-tight text-[#1d1712]">
                TrendWise
              </span>
              <span className="text-[11px] text-[#8a7f72]">Market workspace</span>
            </span>
          </FadeLabel>
          <FadeLabel open={open} delay={nextDelay()} className="ml-auto">
            <span
              className="rounded-full px-1.5 py-0.5 text-[10px] font-bold tracking-wide text-white"
              style={{ backgroundColor: ACCENT }}
            >
              LIVE
            </span>
          </FadeLabel>
        </div>

        {/* Search */}
        <div className="mt-1 px-1">
          {open ? (
            <div
              className="transition-opacity duration-300"
              style={{ opacity: 1, transitionDelay: open ? '90ms' : '0ms' }}
            >
              <SearchBox variant="cream" inputRef={searchRef} />
            </div>
          ) : (
            <button
              type="button"
              aria-label="Search stocks and ETFs"
              title="Search"
              onClick={() => {
                onToggle();
                focusSearch();
              }}
              className="flex h-10 w-10 items-center justify-center rounded-xl border border-[rgba(120,90,40,0.14)] bg-white/70 text-[#5c5347] shadow-sm transition hover:bg-white"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="m21 21-4.35-4.35M17 10.5a6.5 6.5 0 1 1-13 0 6.5 6.5 0 0 1 13 0Z"
                />
              </svg>
            </button>
          )}
        </div>

        {/* Nav */}
        <nav className="no-scrollbar mt-1 flex-1 overflow-y-auto">
          {SECTIONS.map((section) => (
            <div key={section.heading}>
              <p
                className="overflow-hidden px-3 text-[11px] font-semibold text-[#a39a8c] transition-all duration-300"
                style={{
                  opacity: open ? 1 : 0,
                  height: open ? 'auto' : 0,
                  paddingTop: open ? 12 : 0,
                  paddingBottom: open ? 4 : 0,
                  transitionDelay: open ? `${nextDelay()}ms` : '0ms',
                }}
              >
                {section.heading}
              </p>
              <ul className="space-y-0.5">
                {section.items.map((item) => (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      end={item.to === '/'}
                      title={item.label}
                      className={({ isActive }) =>
                        `group relative flex items-center rounded-2xl px-1.5 py-1.5 transition-colors duration-200 ${
                          open ? 'gap-3' : 'gap-0'
                        } ${isActive ? 'bg-[rgba(120,90,40,0.09)]' : 'hover:bg-[rgba(120,90,40,0.05)]'}`
                      }
                    >
                      {({ isActive }) => (
                        <>
                          <Tile color={item.tile} icon={item.icon} />
                          <FadeLabel
                            open={open}
                            delay={nextDelay()}
                            className={`text-sm ${isActive ? 'font-semibold text-[#1d1712]' : 'text-[#3f342a]'}`}
                          >
                            {item.label}
                          </FadeLabel>
                          {!open && (
                            <span className="pointer-events-none absolute left-full top-1/2 z-50 ml-3 -translate-y-1/2 whitespace-nowrap rounded-full border border-white/70 bg-white/95 px-3 py-1.5 text-xs font-semibold text-[#2b2118] opacity-0 shadow-lg transition-opacity duration-200 group-hover:opacity-100">
                              <span className="absolute -left-[5px] top-1/2 h-2.5 w-2.5 -translate-y-1/2 rotate-45 border-b border-l border-white/70 bg-white/95" />
                              {item.label}
                            </span>
                          )}
                        </>
                      )}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div
          className="mt-1 border-t border-[rgba(120,90,40,0.12)] px-3 transition-opacity duration-300"
          style={{
            opacity: open ? 1 : 0,
            height: open ? 'auto' : 0,
            paddingTop: open ? 10 : 0,
            paddingBottom: open ? 6 : 0,
            transitionDelay: open ? '320ms' : '0ms',
          }}
        >
          <p className="whitespace-nowrap text-[10px] leading-relaxed text-[#a39a8c]">
            Educational tool,
            <br />
            not investment advice.
          </p>
        </div>
      </div>

      {/* Collapse button, protruding from the right edge */}
      <button
        type="button"
        onClick={onToggle}
        aria-label={open ? 'Collapse menu' : 'Expand menu'}
        title={open ? 'Collapse' : 'Expand'}
        className="absolute -right-3 top-1/2 z-10 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-full border border-white/70 bg-[#fffdf8] text-[#2b2118] shadow-md transition hover:bg-white"
      >
        <svg
          className="h-4 w-4 transition-transform duration-300"
          style={{ transform: open ? 'rotate(0deg)' : 'rotate(180deg)' }}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth="2.5"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
        </svg>
      </button>
    </aside>
  );
}
