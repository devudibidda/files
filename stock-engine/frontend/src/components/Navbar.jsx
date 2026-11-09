import { NavLink } from 'react-router-dom';
import SearchBox from './SearchBox';

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
      <span className="font-display text-lg font-extrabold tracking-tight text-white">
        Trend<span className="text-gradient">Wise</span>
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
    <header className="sticky top-0 z-40 border-b border-white/10 bg-ink-950/60 backdrop-blur-xl shadow-[0_8px_32px_-16px_rgba(0,0,0,0.8)] md:hidden">
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
