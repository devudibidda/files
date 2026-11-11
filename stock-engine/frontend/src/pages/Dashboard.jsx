import { Link } from 'react-router-dom';
import { api, fmt } from '../api';
import NewsList from '../components/NewsList';
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

function IndexStrip({ indices }) {
  return (
    <div className="flex gap-3 overflow-x-auto pb-1">
      {indices.map((ix, i) => (
        <Reveal key={ix.yahoo} delay={i * 70} className="shrink-0">
          <TiltCard className="h-full">
            <div className="card card-hover h-full min-w-[170px] px-4 py-3">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">{ix.name}</div>
              <div className="num mt-0.5 font-display text-[22px] leading-snug text-slate-100">
                <AnimatedNumber value={ix.price} format={(v) => fmt.num(v)} />
              </div>
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
    <TiltCard className="h-full">
      <div className="card-pad card-hover h-full">
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
    </TiltCard>
  );
}

function MoversTable({ title, rows }) {
  return (
    <TiltCard className="h-full">
      <div className="card card-hover h-full overflow-hidden">
        <div className="px-5 pt-4">
          <SectionTitle>{title}</SectionTitle>
        </div>
        <table className="w-full">
          <tbody>
            {rows.map((r) => (
              <tr key={r.symbol} className="hover:bg-ink-800/60 transition-colors">
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
            <Link to={`/stock/${r.symbol}`} className="card-pad card-hover group block h-full">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="font-bold text-slate-100 group-hover:text-clay transition-colors">{r.symbol}</div>
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

  const asOf = data.computedAt ? data.computedAt.replace('T', ' ').slice(0, 16) : '';

  return (
    <div className="space-y-16">
      {/* Hero: one headline, one supporting line, one action, live indices as the visual */}
      <section>
        <Reveal>
          <p className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">
            <span className="inline-block h-2 w-2 rounded-[2px] bg-clay" aria-hidden />
            NSE · Live{asOf ? ` · Market as of ${asOf}` : ''}
          </p>
          <h1 className="mt-4 max-w-2xl font-display text-[40px] leading-[1.08] text-slate-100 sm:text-[56px]">
            The market,
            <br />
            in plain sight.
          </h1>
          <p className="mt-4 max-w-xl text-[17px] leading-relaxed text-slate-200">
            Live NSE signals, screened every five minutes. Only the calls that clear 60% confidence make the list.
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-5">
            <Link to="/calls" className="btn-dark">
              See today&apos;s calls
            </Link>
            <Link to="/screener" className="text-sm font-semibold text-clay hover:text-clay-deep">
              Open screener →
            </Link>
          </div>
        </Reveal>
        <Reveal delay={120}>
          <div className="mt-10">
            <IndexStrip indices={data.indices} />
          </div>
        </Reveal>
      </section>

      <Reveal delay={80}>
        <div>
          <SectionTitle
            right={
              <Link to="/screener" className="text-xs font-semibold text-clay hover:text-clay-deep">
                Open screener →
              </Link>
            }
          >
            Today&apos;s strong buy signals
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
