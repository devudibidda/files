import { Link } from 'react-router-dom';
import { api, fmt } from '../api';
import NewsList from '../components/NewsList';
import { ChangePct, ErrorNote, Reveal, SectionTitle, Skeleton, SymbolLink, TiltCard, VerdictBadge } from '../components/ui';
import { useFetch } from '../hooks';

function IndexStrip({ indices }) {
  return (
    <div className="flex gap-3 overflow-x-auto pb-1">
      {indices.map((ix, i) => (
        <Reveal key={ix.yahoo} delay={i * 70} className="shrink-0">
          <TiltCard className="h-full">
            <div className="card h-full min-w-[170px] px-4 py-3">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{ix.name}</div>
              <div className="num mt-0.5 text-lg font-bold text-white">{fmt.num(ix.price)}</div>
              <ChangePct value={ix.changePct} className="text-xs" />
            </div>
          </TiltCard>
        </Reveal>
      ))}
    </div>
  );
}

function BreadthBar({ breadth }) {
  const total = breadth.advancers + breadth.decliners + breadth.unchanged || 1;
  const advPct = (breadth.advancers / total) * 100;
  return (
    <div className="card-pad card-hover">
      <SectionTitle>Market breadth</SectionTitle>
      <div className="flex h-3 overflow-hidden rounded-full bg-ink-700">
        <div className="bg-bull/80" style={{ width: `${advPct}%` }} />
        <div className="bg-bear/80" style={{ width: `${100 - advPct}%` }} />
      </div>
      <div className="mt-2 flex justify-between text-xs">
        <span className="text-bull font-semibold">{breadth.advancers} advancing</span>
        <span className="text-bear font-semibold">{breadth.decliners} declining</span>
      </div>
    </div>
  );
}

function MoversTable({ title, rows }) {
  return (
    <div className="card card-hover overflow-hidden">
      <div className="px-5 pt-4">
        <SectionTitle>{title}</SectionTitle>
      </div>
      <table className="w-full">
        <tbody>
          {rows.map((r) => (
            <tr key={r.symbol} className="hover:bg-ink-700/40 transition-colors">
              <td className="table-cell">
                <SymbolLink symbol={r.symbol} name={r.name} />
              </td>
              <td className="table-cell num text-right text-slate-300">{fmt.price(r.price)}</td>
              <td className="table-cell text-right">
                <ChangePct value={r.changePct} className="text-xs" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
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
  if (!rows.length) return <p className="text-sm text-slate-500">No Strong Buy signals right now.</p>;
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {rows.map((r, i) => (
        <Reveal key={r.symbol} delay={i * 70}>
          <TiltCard className="h-full">
            <Link to={`/stock/${r.symbol}`} className="card-pad group block h-full">
          <div className="flex items-start justify-between gap-2">
            <div>
              <div className="font-bold text-slate-100 group-hover:text-brand-400 transition-colors">{r.symbol}</div>
              <div className="mt-0.5 line-clamp-1 text-xs text-slate-500">{r.name}</div>
            </div>
            <VerdictBadge verdict={r.verdict} />
          </div>
          <div className="mt-3 flex items-end justify-between">
            <span className="num text-lg font-bold text-white">{fmt.price(r.price)}</span>
            <span className="text-xs text-slate-500">
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

export default function Dashboard() {
  const { data, error, loading, retry } = useFetch(() => api.overview(), []);
  const news = useFetch(() => api.marketNews(), []);

  if (loading)
    return (
      <div className="space-y-4">
        <Skeleton className="h-20" />
        <div className="grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  if (error) return <ErrorNote error={error} retry={retry} />;

  return (
    <div className="space-y-6">
      {data.computedAt && (
        <p className="text-xs text-slate-500">Market as of {data.computedAt.replace('T', ' ').slice(0, 16)}</p>
      )}
      <Reveal>
        <IndexStrip indices={data.indices} />
      </Reveal>

      <Reveal delay={80}>
      <div>
        <SectionTitle
          right={
            <Link to="/screener" className="text-xs font-semibold text-brand-400 hover:text-brand-500">
              Open screener →
            </Link>
          }
        >
          Today's strong buy signals
        </SectionTitle>
        <StrongBuys />
      </div>
      </Reveal>

      <Reveal delay={120}>
      <div className="grid gap-4 lg:grid-cols-3">
        <MoversTable title="Top gainers" rows={data.topGainers} />
        <MoversTable title="Top losers" rows={data.topLosers} />
        <BreadthBar breadth={data.breadth} />
      </div>
      </Reveal>

      <Reveal delay={160}>
      <div className="card-pad card-hover">
        <SectionTitle>Market news</SectionTitle>
        {news.loading ? <Skeleton className="h-40" /> : <NewsList items={news.data?.items?.slice(0, 10)} />}
      </div>
      </Reveal>
    </div>
  );
}
