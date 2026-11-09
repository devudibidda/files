import { useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import CallsPage from './pages/CallsPage';
import Dashboard from './pages/Dashboard';
import EtfPage from './pages/EtfPage';
import MutualFundsPage from './pages/MutualFundsPage';
import ScreenerPage from './pages/ScreenerPage';
import StockPage from './pages/StockPage';
import WatchlistPage from './pages/WatchlistPage';

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(() => {
    try {
      return localStorage.getItem('tw-sidebar') !== 'collapsed';
    } catch {
      return true;
    }
  });

  const toggleSidebar = () => {
    setSidebarOpen((o) => {
      const next = !o;
      try {
        localStorage.setItem('tw-sidebar', next ? 'open' : 'collapsed');
      } catch {}
      return next;
    });
  };

  return (
    <div className="min-h-screen">
      <div className="relative z-10">
        <Navbar />
        <Sidebar open={sidebarOpen} onToggle={toggleSidebar} />
        <div
          className={`transition-[margin] duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] ${
            sidebarOpen ? 'md:ml-[312px]' : 'md:ml-[104px]'
          }`}
        >
          <main className="mx-auto max-w-7xl px-4 sm:px-6 pb-16 pt-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/stock/:symbol" element={<StockPage />} />
              <Route path="/screener" element={<ScreenerPage />} />
              <Route path="/calls" element={<CallsPage />} />
              <Route path="/start" element={<Navigate to="/" replace />} />
              <Route path="/etfs" element={<EtfPage />} />
              <Route path="/mutual-funds" element={<MutualFundsPage />} />
              <Route path="/watchlist" element={<WatchlistPage />} />
            </Routes>
          </main>
          <footer className="border-t border-ink-700 py-6">
            <p className="mx-auto max-w-7xl px-6 text-xs leading-relaxed text-slate-500">
              TrendWise is an educational analysis tool, not SEBI-registered investment advice. Technical signals are
              probabilistic, not guarantees, markets carry risk. Always do your own research before trading.
            </p>
          </footer>
        </div>
      </div>
    </div>
  );
}
