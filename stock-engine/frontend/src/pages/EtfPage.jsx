import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api, fmt } from '../api';
import { ChangePct, ErrorNote, Reveal, SectionTitle, Skeleton, SymbolLink, VerdictBadge } from '../components/ui';
import { useFetch } from '../hooks';

export default function EtfPage() {
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState(null);
  const { data, error, loading, retry } = useFetch(() => api.screener('all', 'etf'), []);
  const leaders = useFetch(() => api.etfLeaders(), []);

  const refresh = async () => {
    setRefreshing(true);
    setRefreshError(null);
    try {
      await api.refreshEtfLeaders();
      retry();
      leaders.retry();
    } catch (e) {
      setRefreshError(e.message);
    } finally {
      setRefreshing(false);
    }
  };

  if (loading) return <Skeleton className="h-96" />;
  if (error) return <ErrorNote error={error} retry={retry} />;

  const rows = data?.results || [];
  const cats = leaders.data?.categories || [];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-display text-2xl text-slate-100">ETF hub</h1>
        <p className="mt-1 text-sm text-slate-500">
          Curated NSE-listed ETFs - index, gold, sector, factor and international - ranked by composite signal score.
        </p>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <span className="text-xs text-slate-500">
            {leaders.data?.computedAt ? `Signals as of ${leaders.data.computedAt.replace('T', ' ').slice(0, 16)}` : 'Signals load from the latest scan'}
          </span>
          <button onClick={refresh} disabled={refreshing} className="btn-pill">
            {refreshing ? 'Refreshing…' : 'Refresh signals'}
          </button>
          {refreshError && <span className="text-xs text-rose-300">{refreshError}</span>}
        </div>
      </div>

      {cats.length > 0 && (
        <Reveal><div className="card-pad card-hover">
          <SectionTitle>Top picks per category</SectionTitle>
          <div className="grid items-stretch gap-4 md:grid-cols-2 xl:grid-cols-3">
            {cats.map((c) => (
              <div
                key={c.category}
                className="flex h-full flex-col rounded-2xl border border-ink-700 bg-ivory/60 p-4 shadow-[inset_0_1px_0_#ffffff,0_1px_2px_rgba(43,33,24,0.08)]"
              >
                <div className="flex items-center justify-between gap-2 border-b border-ink-700 pb-2">
                  <span className="text-[11px] font-bold uppercase tracking-wide text-slate-300">{c.category}</span>
                  <span className="chip bg-ink-700 text-slate-300">
                    {c.leaders.length} {c.leaders.length === 1 ? 'pick' : 'picks'}
                  </span>
                </div>
                <div className="mt-1 flex-1">
                  {c.leaders.map((r) => (
                    <Link
                      key={r.symbol}
                      to={`/stock/${r.symbol}`}
                      className="group flex items-center justify-between gap-3 border-b border-ink-700/60 py-2 last:border-b-0"
                    >
                      <span className="min-w-0">
                        <span className="block font-semibold text-slate-100 transition-colors group-hover:text-clay">
                          {r.symbol}
                        </span>
                        <span className="block truncate text-xs text-slate-500">{r.name}</span>
                      </span>
                      <span className="flex shrink-0 items-center gap-2">
                        <span className={`num text-sm font-bold ${r.score >= 0 ? 'text-bull' : 'text-bear'}`}>
                          {r.score > 0 ? `+${r.score}` : r.score}
                        </span>
                        <VerdictBadge verdict={r.verdict} />
                      </span>
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <p className="mt-3 text-[11px] leading-relaxed text-slate-500">{leaders.data.method}</p>
        </div></Reveal>
      )}

      <Reveal><div className="card card-hover overflow-hidden">
        <div className="px-5 pt-4">
          <SectionTitle>Analyzed ETFs (ranked by score)</SectionTitle>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px]">
            <thead>
              <tr>
                <th className="table-head">ETF</th>
                <th className="table-head text-right">Price</th>
                <th className="table-head text-right">Score</th>
                <th className="table-head">Verdict</th>
                <th className="table-head text-right">RSI</th>
                <th className="table-head text-right">vs 52w high</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.symbol} className="hover:bg-ink-700/40 transition-colors">
                  <td className="table-cell">
                    <SymbolLink symbol={r.symbol} name={r.name} />
                  </td>
                  <td className="table-cell num text-right text-slate-200">{fmt.price(r.price)}</td>
                  <td className="table-cell num text-right">
                    <span className={`font-bold ${r.score >= 0 ? 'text-bull' : 'text-bear'}`}>
                      {r.score > 0 ? `+${r.score}` : r.score}
                    </span>
                  </td>
                  <td className="table-cell">
                    <VerdictBadge verdict={r.verdict} />
                  </td>
                  <td className="table-cell num text-right text-slate-300">{r.rsi?.toFixed(0) ?? '-'}</td>
                  <td className="table-cell text-right">
                    <ChangePct value={r.distFromHigh52wPct} className="text-xs" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {rows.length === 0 && <p className="py-10 text-center text-sm text-slate-500">ETF data is still loading on the server, try again shortly.</p>}
        </div>
      </div></Reveal>
    </div>
  );
}
