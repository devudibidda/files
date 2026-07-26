const BASE = import.meta.env.VITE_API_URL || '';

async function get(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export const api = {
  health: () => get('/api/health'),
  search: (q) => get(`/api/symbols/search?q=${encodeURIComponent(q)}`),
  quote: (symbol) => get(`/api/stocks/${symbol}/quote`),
  history: (symbol, range) => get(`/api/stocks/${symbol}/history?range=${range}`),
  analysis: (symbol) => get(`/api/stocks/${symbol}/analysis`),
  stockNews: (symbol) => get(`/api/stocks/${symbol}/news`),
  marketNews: () => get('/api/news/market'),
  overview: () => get('/api/market/overview'),
  scans: () => get('/api/screener/scans'),
  screener: (scan, type) =>
    get(`/api/screener?scan=${scan}${type ? `&type=${type}` : ''}`),
  etfs: () => get('/api/etfs'),
  watchlist: {
    get: (clientId) => get(`/api/watchlist?client_id=${clientId}`),
    add: (clientId, symbol) =>
      fetch(`${BASE}/api/watchlist?client_id=${clientId}&symbol=${symbol}`, { method: 'POST' }).then((r) => r.json()),
    remove: (clientId, symbol) =>
      fetch(`${BASE}/api/watchlist?client_id=${clientId}&symbol=${symbol}`, { method: 'DELETE' }).then((r) => r.json()),
  },
};

export function clientId() {
  let id = localStorage.getItem('tw-client-id');
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem('tw-client-id', id);
  }
  return id;
}

export const fmt = {
  price: (v) =>
    v == null ? '—' : `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 2, minimumFractionDigits: 2 })}`,
  pct: (v) => (v == null ? '—' : `${v > 0 ? '+' : ''}${Number(v).toFixed(2)}%`),
  num: (v) => (v == null ? '—' : Number(v).toLocaleString('en-IN')),
  compact: (v) => {
    if (v == null) return '—';
    if (v >= 1e7) return `${(v / 1e7).toFixed(1)} Cr`;
    if (v >= 1e5) return `${(v / 1e5).toFixed(1)} L`;
    return Number(v).toLocaleString('en-IN');
  },
  timeAgo: (epoch) => {
    if (!epoch) return '';
    const s = Math.floor(Date.now() / 1000 - epoch);
    if (s < 3600) return `${Math.max(1, Math.floor(s / 60))}m ago`;
    if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
    return `${Math.floor(s / 86400)}d ago`;
  },
};

export const verdictColor = (verdict) =>
  ({
    'Strong Buy': 'text-bull bg-bull/10 ring-1 ring-bull/30',
    Buy: 'text-emerald-300 bg-emerald-500/10 ring-1 ring-emerald-400/25',
    Hold: 'text-amber-300 bg-amber-400/10 ring-1 ring-amber-400/25',
    Sell: 'text-rose-300 bg-rose-500/10 ring-1 ring-rose-400/25',
    'Strong Sell': 'text-bear bg-bear/10 ring-1 ring-bear/30',
  })[verdict] || 'text-slate-300 bg-ink-700';
