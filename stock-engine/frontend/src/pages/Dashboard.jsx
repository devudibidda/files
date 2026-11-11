import { Link } from 'react-router-dom';
import { api, fmt } from '../api';
import NewsList from '../components/NewsList';
import SearchBox from '../components/SearchBox';
import {
  AnimatedNumber,
  ChangePct,
  ErrorNote,
  Reveal,
  SectionTitle,
  Skeleton,
  SymbolLink,
  TiltCard,
  VerdictBadge,
} from '../components/ui';
import { useFetch } from '../hooks';

/* Glassy Dashboard V24 (code.xr reel, Nov 11 2026).
   Light glassmorphism dashboard: translucent white cards over a soft
   gradient-blob canvas, violet primary accent, pink chart. The layout
   follows the reel: greeting header + search, four stat cards, an
   analytics area chart beside a progress donut, and a movers table.
   Content is TrendWise market data, not the reel's SaaS numbers. */

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

function StatCard({ icon, chipBg, label, value, change, sub, delay = 0 }) {
  return (
    <Reveal delay={delay}>
      <TiltCard className="h-full">
        <div className="glass-card glass-card-hover flex h-full items-start gap-3 p-5">
          <span className="v24-icon-chip" style={{ background: chipBg }}>
            {icon}
          </span>
          <div className="min-w-0">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">{label}</div>
            <div className="num mt-1 font-display text-[26px] leading-none text-slate-100">
              <AnimatedNumber value={value} format={(v) => fmt.num(v)} />
            </div>
            <div className="mt-1.5 flex items-center gap-1.5">
              {change != null && <ChangePct value={change} className="text-xs" />}
              {sub && <span className="text-xs text-slate-400">{sub}</span>}
            </div>
          </div>
        </div>
      </TiltCard>
    </Reveal>
  );
}

const ICONS = {
  chart: (
    <svg className="h-5 w-5 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 17l5.5-5.5 3.5 3.5L21 6" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 6h6v6" />
    </svg>
  ),
  bank: (
    <svg className="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 9.5 12 4l9 5.5M5 10v8M9.5 10v8M14.5 10v8M19 10v8M3 20h18" />
    </svg>
  ),
  bolt: (
    <svg className="h-5 w-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M13 2 4.5 13.5H11L9.5 22 19 10h-6.5L13 2Z" />
    </svg>
  ),
  users: (
    <svg className="h-5 w-5 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M16 19v-1a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v1M9 10a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM22 19v-1a4 4 0 0 0-3-3.87M15 3.13a3 3 0 0 1 0 5.74" />
    </svg>
  ),
};

/* Smooth SVG area chart for the Nifty 50, last 10 trading days.
   Catmull-Rom to Bezier smoothing, pink line over a pink-to-violet
   gradient fill. No chart library, so no new dependency. */
function NiftyChart() {
  const { data, loading } = useFetch(() => api.history('^NSEI', '1M'), []);
  if (loading) return <Skeleton className="h-56" />;
  const candles = (data?.candles || []).slice(-10);
  if (candles.length < 3) return <p className="text-sm text-slate-400">Nifty history is unavailable right now.</p>;

  const closes = candles.map((c) => c.close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const span = max - min || 1;
  const W = 560;
  const H = 220;
  const padX = 8;
  const padY = 18;
  const pts = closes.map((v, i) => ({
    x: padX + (i * (W - padX * 2)) / (closes.length - 1),
    y: padY + (1 - (v - min) / span) * (H - padY * 2),
  }));
  // Catmull-Rom to cubic Bezier
  let d = `M ${pts[0].x} ${pts[0].y}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[Math.min(pts.length - 1, i + 2)];
    const c1x = p1.x + (p2.x - p0.x) / 6;
    const c1y = p1.y + (p2.y - p0.y) / 6;
    const c2x = p2.x - (p3.x - p1.x) / 6;
    const c2y = p2.y - (p3.y - p1.y) / 6;
    d += ` C ${c1x} ${c1y}, ${c2x} ${c2y}, ${p2.x} ${p2.y}`;
  }
  const area = `${d} L ${pts[pts.length - 1].x} ${H - 4} L ${pts[0].x} ${H - 4} Z`;
  const change = ((closes[closes.length - 1] - closes[0]) / closes[0]) * 100;
  const dayName = (t) => new Date(`${t}T12:00:00+05:30`).toLocaleDateString('en-IN', { weekday: 'short' });

  return (
    <div>
      <div className="flex items-center gap-2">
        <span className={`chip ${change >= 0 ? 'bg-bull/10 text-bull' : 'bg-bear/10 text-bear'}`}>
          {change >= 0 ? '▲' : '▼'} {Math.abs(change).toFixed(1)}%
        </span>
        <span className="text-xs text-slate-400">Last {candles.length} sessions</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="mt-3 w-full" role="img" aria-label="Nifty 50 trend">
        <defs>
          <linearGradient id="v24-area" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ec4899" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.04" />
          </linearGradient>
        </defs>
        {[0.25, 0.5, 0.75].map((f) => (
          <line key={f} x1={padX} x2={W - padX} y1={H * f} y2={H * f} stroke="#e3dacc" strokeWidth="1" />
        ))}
        <path d={area} fill="url(#v24-area)" />
        <path d={d} fill="none" stroke="#ec4899" strokeWidth="2.5" strokeLinecap="round" />
        <circle cx={pts[pts.length - 1].x} cy={pts[pts.length - 1].y} r="4.5" fill="#ec4899" stroke="#fff" strokeWidth="2" />
      </svg>
      <div className="mt-1 flex justify-between text-[11px] text-slate-400">
        {candles.map((c, i) =>
          i % 2 === 0 || i === candles.length - 1 ? <span key={c.time}>{dayName(c.time)}</span> : <span key={c.time} />,
        )}
      </div>
    </div>
  );
}

/* Market breadth as a donut: advancers / decliners / unchanged. */
function BreadthDonut({ breadth }) {
  const total = breadth.advancers + breadth.decliners + breadth.unchanged || 1;
  const adv = (breadth.advancers / total) * 100;
  const dec = (breadth.decliners / total) * 100;
  const r = 54;
  const C = 2 * Math.PI * r;
  const advLen = (adv / 100) * C;
  const decLen = (dec / 100) * C;
  return (
    <div className="flex items-center gap-5">
      <svg width="140" height="140" viewBox="0 0 140 140" className="-rotate-90">
        <circle cx="70" cy="70" r={r} fill="none" stroke="#e3dacc" strokeWidth="14" />
        <circle
          cx="70" cy="70" r={r} fill="none" stroke="#02a745" strokeWidth="14"
          strokeDasharray={`${advLen} ${C - advLen}`} strokeLinecap="round"
        />
        <circle
          cx="70" cy="70" r={r} fill="none" stroke="#a10214" strokeWidth="14"
          strokeDasharray={`${decLen} ${C - decLen}`} strokeDashoffset={-advLen} strokeLinecap="round"
        />
        <g transform="rotate(90 70 70)">
          <text x="70" y="66" textAnchor="middle" className="fill-slate-100" fontSize="24" fontWeight="700">
            {Math.round(adv)}%
          </text>
          <text x="70" y="84" textAnchor="middle" className="fill-slate-400" fontSize="11">
            advancing
          </text>
        </g>
      </svg>
      <ul className="space-y-2 text-sm">
        <li className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-bull" />
          <span className="text-slate-200">Advancing</span>
          <span className="num ml-auto font-semibold text-slate-100">{breadth.advancers}</span>
        </li>
        <li className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-bear" />
          <span className="text-slate-200">Declining</span>
          <span className="num ml-auto font-semibold text-slate-100">{breadth.decliners}</span>
        </li>
        <li className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-[#b0aea5]" />
          <span className="text-slate-200">Unchanged</span>
          <span className="num ml-auto font-semibold text-slate-100">{breadth.unchanged}</span>
        </li>
      </ul>
    </div>
  );
}

function MoversTable({ title, rows, tone }) {
  return (
    <TiltCard className="h-full">
      <div className="glass-card glass-card-hover h-full overflow-hidden">
        <div className="flex items-center justify-between px-5 pt-4">
          <h3 className="font-display text-xl text-slate-100">{title}</h3>
          <Link to="/screener" className="text-xs font-semibold text-violet-600 hover:text-violet-700">
            Open screener →
          </Link>
        </div>
        <table className="mt-2 w-full">
          <tbody>
            {rows.map((r) => (
              <tr key={r.symbol} className="transition-colors hover:bg-violet-500/5">
                <td className="table-cell">
                  <SymbolLink symbol={r.symbol} name={r.name} />
                </td>
                <td className="table-cell num text-right text-slate-200">{fmt.price(r.price)}</td>
                <td className="table-cell text-right">
                  <ChangePct value={r.changePct} className="text-xs" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </TiltCard>
  );
}

function StrongBuys() {
  const { data, loading } = useFetch(() => api.screener('strong_buy'), []);
  if (loading)
    return (
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-28" />
        ))}
      </div>
    );
  const rows = data?.results?.slice(0, 6) || [];
  if (!rows.length) return <p className="text-sm text-slate-400">No Strong Buy signals right now.</p>;
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {rows.map((r, i) => (
        <Reveal key={r.symbol} delay={i * 70}>
          <TiltCard className="h-full">
            <Link to={`/stock/${r.symbol}`} className="glass-card glass-card-hover group block h-full p-5">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="font-bold text-slate-100 group-hover:text-violet-600 transition-colors">{r.symbol}</div>
                  <div className="mt-0.5 line-clamp-1 text-xs text-slate-400">{r.name}</div>
                </div>
                <VerdictBadge verdict={r.verdict} />
              </div>
              <div className="mt-3 flex items-end justify-between">
                <span className="num text-lg font-bold text-slate-100">{fmt.price(r.price)}</span>
                <span className="text-xs text-slate-400">
                  Score <span className="num font-bold text-bull">+{r.score}</span>
                </span>
              </div>
            </Link>
          </TiltCard>
        </Reveal>
      ))}
    </div>
  );
}

function StrongBuyStat({ delay = 0 }) {
  const { data, loading } = useFetch(() => api.screener('strong_buy'), []);
  const count = data?.results?.length ?? 0;
  return (
    <StatCard
      icon={ICONS.bolt} chipBg="rgba(16,185,129,0.14)" label="Strong buys"
      value={loading ? null : count} change={null}
      sub={loading ? 'loading…' : 'signals above 60% confidence'} delay={delay}
    />
  );
}

export default function Dashboard() {
  const { data, error, loading, retry } = useFetch(() => api.overview(), []);
  const news = useFetch(() => api.marketNews(), []);

  if (loading)
    return (
      <div className="v24-page -mx-4 -mt-6 -mb-16 space-y-4 px-4 pb-16 pt-8 sm:-mx-6 sm:px-6">
        <Skeleton className="h-20" />
        <div className="grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  if (error) return <ErrorNote error={error} retry={retry} />;

  const asOf = data.computedAt ? data.computedAt.replace('T', ' ').slice(0, 16) : '';
  const nifty = data.indices.find((i) => i.name === 'NIFTY 50');
  const sensex = data.indices.find((i) => i.name === 'SENSEX');
  const totalBreadth = data.breadth.advancers + data.breadth.decliners + data.breadth.unchanged || 1;
  const advPct = (data.breadth.advancers / totalBreadth) * 100;

  return (
    <div className="v24-page -mx-4 -mt-6 -mb-16 space-y-6 px-4 pb-16 pt-8 sm:-mx-6 sm:px-6">
      {/* Header: greeting, search, live pill */}
      <Reveal>
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="font-display text-[34px] leading-none text-slate-100 sm:text-[40px]">Dashboard</h1>
            <p className="mt-2 text-sm text-slate-400">
              {greeting()}, here&apos;s what&apos;s happening in the market today
              {asOf ? ` · as of ${asOf}` : ''}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="chip bg-violet-600/10 text-violet-700 ring-1 ring-violet-500/30">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-violet-500 opacity-60" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-violet-600" />
              </span>
              LIVE
            </span>
            <div className="w-64 max-w-full">
              <SearchBox variant="cream" />
            </div>
          </div>
        </div>
      </Reveal>

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={ICONS.chart} chipBg="rgba(139,92,246,0.14)" label="Nifty 50"
          value={nifty?.price} change={nifty?.changePct} sub="index" delay={0}
        />
        <StatCard
          icon={ICONS.bank} chipBg="rgba(59,130,246,0.14)" label="Sensex"
          value={sensex?.price} change={sensex?.changePct} sub="index" delay={60}
        />
        <StrongBuyStat delay={120} />
        <StatCard
          icon={ICONS.users} chipBg="rgba(245,158,11,0.16)" label="Advancing"
          value={data.breadth.advancers} change={null} sub={`of ${totalBreadth} tracked · ${advPct.toFixed(0)}%`} delay={180}
        />
      </div>

      {/* Analytics chart + breadth donut */}
      <div className="grid gap-4 lg:grid-cols-5">
        <Reveal delay={80} className="lg:col-span-3">
          <div className="glass-card glass-card-hover h-full p-5 sm:p-6">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-xl text-slate-100">Analytics overview</h3>
              <span className="chip bg-ink-700 text-slate-200">Nifty 50 · Last 10 sessions</span>
            </div>
            <div className="mt-4">
              <NiftyChart />
            </div>
          </div>
        </Reveal>
        <Reveal delay={140} className="lg:col-span-2">
          <div className="glass-card glass-card-hover h-full p-5 sm:p-6">
            <h3 className="font-display text-xl text-slate-100">Market breadth</h3>
            <p className="mt-1 text-xs text-slate-400">Advancers vs decliners across the tracked universe</p>
            <div className="mt-5">
              <BreadthDonut breadth={data.breadth} />
            </div>
          </div>
        </Reveal>
      </div>

      {/* Movers */}
      <Reveal delay={100}>
        <div className="grid gap-4 lg:grid-cols-2">
          <MoversTable title="Top gainers" rows={data.topGainers} />
          <MoversTable title="Top losers" rows={data.topLosers} />
        </div>
      </Reveal>

      {/* Strong buys */}
      <Reveal delay={80}>
        <div>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-display text-2xl text-slate-100">Today&apos;s strong buy signals</h2>
            <Link to="/screener" className="text-xs font-semibold text-violet-600 hover:text-violet-700">
              Open screener →
            </Link>
          </div>
          <StrongBuys />
        </div>
      </Reveal>

      {/* News */}
      <Reveal delay={120}>
        <div className="glass-card p-5 sm:p-6">
          <h2 className="font-display text-2xl text-slate-100">Market news</h2>
          <div className="mt-3">
            {news.loading ? <Skeleton className="h-40" /> : <NewsList items={news.data?.items?.slice(0, 10)} />}
          </div>
        </div>
      </Reveal>
    </div>
  );
}
