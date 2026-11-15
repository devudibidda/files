import { NavLink } from 'react-router-dom';
import SearchBox from './SearchBox';

function Logo() {
  return (
    <NavLink to="/" className="flex shrink-0 items-center gap-2.5">
      <span className="skeuo-medallion flex h-8 w-8 items-center justify-center rounded-lg">
        <svg viewBox="0 0 32 32" className="h-5 w-5">
          <path
            d="M6 22 L13 14 L18 18 L26 8"
            stroke="#d97757"
            strokeWidth="3"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      <span className="font-display text-lg font-semibold tracking-tight text-[#2b2118]">
        Trend<span className="text-clay">Wise</span>
      </span>
    </NavLink>
  );
}

/**
 * Mobile-only top bar. On desktop (md and up) the leather sidebar
 * (components/Sidebar.jsx) is the menu, so this header hides there.
 * The hamburger opens the sidebar as a slide-in drawer; the old
 * horizontally scrolling pill row is gone (the drawer is the one menu).
 */
export default function Navbar({ onOpenMenu }) {
  return (
    <header className="skeuo-metal mobile-bar sticky top-0 z-40 md:hidden">
      <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-3 sm:px-6">
        <button
          type="button"
          onClick={onOpenMenu}
          aria-label="Open menu"
          className="skeuo-knob flex h-11 w-11 shrink-0 items-center justify-center rounded-xl"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5M3.75 17.25h16.5" />
          </svg>
        </button>
        <Logo />
        <div className="ml-auto min-w-0 flex-1 md:max-w-md">
          <SearchBox variant="cream" />
        </div>
      </div>
    </header>
  );
}
