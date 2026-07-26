import { Route, Routes } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import EtfPage from './pages/EtfPage';
import ScreenerPage from './pages/ScreenerPage';
import StockPage from './pages/StockPage';
import WatchlistPage from './pages/WatchlistPage';

export default function App() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 sm:px-6 pb-16 pt-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/stock/:symbol" element={<StockPage />} />
          <Route path="/screener" element={<ScreenerPage />} />
          <Route path="/etfs" element={<EtfPage />} />
          <Route path="/watchlist" element={<WatchlistPage />} />
        </Routes>
      </main>
      <footer className="border-t border-ink-700 py-6">
        <p className="mx-auto max-w-7xl px-6 text-xs leading-relaxed text-slate-500">
          TrendWise is an educational analysis tool, not SEBI-registered investment advice. Technical signals are
          probabilistic, not guarantees — markets carry risk. Always do your own research before trading.
        </p>
      </footer>
    </div>
  );
}
