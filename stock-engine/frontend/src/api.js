const BASE = import.meta.env.VITE_API_URL || '';

async function get(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

async function post(path) {
  const res = await fetch(`${BASE}${path}`, { method: 'POST' });
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
  analysis: (symbol, accountSize = 100000, riskPct = 1) =>
    get(`/api/stocks/${symbol}/analysis?account_size=${accountSize}&risk_pct=${riskPct}`),
  backtest: (symbol) => get(`/api/stocks/${symbol}/backtest`),
  aiAnalysis: (symbol) => get(`/api/stocks/${symbol}/ai-analysis`),
  refreshAiAnalysis: (symbol) => post(`/api/stocks/${symbol}/ai-analysis/refresh`),
  stockNews: (symbol) => get(`/api/stocks/${symbol}/news`),
  marketNews: () => get('/api/news/market'),
  overview: () => get('/api/market/overview'),
  scans: () => get('/api/screener/scans'),
  screener: (scan, type) =>
    get(`/api/screener?scan=${scan}${type ? `&type=${type}` : ''}`),
  etfs: () => get('/api/etfs'),
  etfLeaders: () => get('/api/etfs/leaders'),
  refreshEtfLeaders: () => post('/api/etfs/leaders/refresh'),
  calls: () => get('/api/calls'),
  refreshScreener: () => post('/api/screener/refresh'),
  mfSearch: (q) => get(`/api/mutual-funds/search?q=${encodeURIComponent(q)}`),
  mfDetail: (code) => get(`/api/mutual-funds/${code}`),
  mfLeaders: (category) => get(`/api/mutual-funds/leaders?category=${encodeURIComponent(category)}`),
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
    id = newId();
    localStorage.setItem('tw-client-id', id);
  }
  return id;
}

// crypto.randomUUID() only exists in secure contexts (https or localhost).
// The VM site runs on plain http, so it is undefined there and throws.
// Fall back to getRandomValues (available everywhere), then Math.random.
function newId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
    const b = new Uint8Array(16);
    crypto.getRandomValues(b);
    b[6] = (b[6] & 0x0f) | 0x40;
    b[8] = (b[8] & 0x3f) | 0x80;
    const hex = [...b].map((x) => x.toString(16).padStart(2, '0')).join('');
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
  }
  return `tw-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

export const fmt = {
  price: (v) =>
    v == null ? '-' : `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 2, minimumFractionDigits: 2 })}`,
  pct: (v) => (v == null ? '-' : `${v > 0 ? '+' : ''}${Number(v).toFixed(2)}%`),
  num: (v) => (v == null ? '-' : Number(v).toLocaleString('en-IN')),
  compact: (v) => {
    if (v == null) return '-';
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
