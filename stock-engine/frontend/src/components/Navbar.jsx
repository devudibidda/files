import { NavLink } from 'react-router-dom';
import SearchBox from './SearchBox';

function Logo() {
  return (
    <NavLink to="/" className="flex items-center gap-2.5 shrink-0">
      <svg viewBox="0 0 32 32" className="h-8 w-8">
        <rect width="32" height="32" rx="8" fill="#121212" />
        <path
          d="M6 22 L13 14 L18 18 L26 8"
          className="stroke-bull"
          strokeWidth="3"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span className="font-display text-lg font-semibold tracking-tight text-slate-100">
        Trend<span className="text-clay">Wise</span>
      </span>
    </NavLink>
  );
}

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/screener', label: 'Screener' },
  { to: '/calls', label: 'Calls' },
  { to: '/etfs', label: 'ETFs' },
  { to: '/mutual-funds', label: 'Mutual Funds' },
  { to: '/watchlist', label: 'Watchlist' },
];

/**
 * Mobile-only top bar. On desktop (md and up) the glassy sidebar
 * (components/Sidebar.jsx) is the menu, so this header hides there.
 */
export default function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-ink-700 bg-paper/80 backdrop-blur-xl shadow-[0_8px_24px_-16px_rgba(18,18,18,0.15)] md:hidden">
      <div className="mx-auto flex max-w-7xl items-center gap-6 px-4 py-3 sm:px-6">
        <Logo />
        <div className="ml-auto flex-1 md:max-w-md">
          <SearchBox variant="dark" />
        </div>
      </div>
      <nav className="flex items-center gap-1 overflow-x-auto px-4 pb-2">
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
