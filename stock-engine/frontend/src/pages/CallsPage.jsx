import { useState } from 'react';
import { api, fmt } from '../api';
import { ErrorNote, Reveal, SectionTitle, Skeleton, SymbolLink, VerdictBadge } from '../components/ui';
import { useFetch } from '../hooks';

const actionLabel = (action) =>
  ({ BUY: 'Buy now', BUY_ON_DIP: 'Buy on dip', AVOID_OR_EXIT: 'Exit / avoid' })[action] || action;

function CallCard({ call, side }) {
  return (
    <div className="card-pad card-hover">
      <div className="flex items-start justify-between gap-2">
        <SymbolLink symbol={call.symbol} name={call.name} />
        <VerdictBadge verdict={call.verdict} />
      </div>
      <div className="mt-3 flex items-baseline gap-3">
        <span className="num text-lg font-bold text-slate-100">{fmt.price(call.price)}</span>
        <span className={`num text-sm font-bold ${call.score >= 0 ? 'text-bull' : 'text-bear'}`}>
          {call.score > 0 ? `+${call.score}` : call.score}
        </span>
        <span className="text-xs text-slate-500">Confidence {call.confidence}%</span>
      </div>
      <div className="mt-1 text-xs font-semibold text-slate-300">{actionLabel(call.action)}</div>
      {call.summary && <p className="mt-2 text-xs leading-relaxed text-slate-400">{call.summary}</p>}
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
        {side === 'buy' && (
          <>
            <div>
              <div className="text-[10px] uppercase tracking-wide text-slate-500">Entry zone</div>
              <div className="num mt-0.5 font-semibold text-slate-200">
                {call.entryZone ? `${fmt.price(call.entryZone[0])} - ${fmt.price(call.entryZone[1])}` : '-'}
              </div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wide text-slate-500">Stop loss</div>
              <div className="num mt-0.5 font-semibold text-rose-300">{fmt.price(call.stopLoss)}</div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wide text-slate-500">Target 1</div>
              <div className="num mt-0.5 font-semibold text-bull">{fmt.price(call.target1)}</div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wide text-slate-500">Target 2</div>
              <div className="num mt-0.5 font-semibold text-bull">{fmt.price(call.target2)}</div>
            </div>
          </>
        )}
        {side === 'sell' && (
          <div className="col-span-2">
            <div className="text-[10px] uppercase tracking-wide text-slate-500">Invalidation level</div>
            <div className="num mt-0.5 font-semibold text-slate-200">
              A recovery above {fmt.price(call.stopLoss)} would negate the bearish setup.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function CallsPage() {
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState(null);
  const { data, error, loading, retry } = useFetch(() => api.calls(), []);

  const refresh = async () => {
    setRefreshing(true);
    setRefreshError(null);
    try {
      await api.refreshScreener();
      retry();
    } catch (e) {
      setRefreshError(e.message);
    } finally {
      setRefreshing(false);
    }
  };

  if (loading) return <Skeleton className="h-96" />;
  if (error) return <ErrorNote error={error} retry={retry} />;

  const buys = data?.buyCalls || [];
  const sells = data?.sellCalls || [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-2xl text-slate-100">Signal calls</h1>
        <p className="mt-1 text-sm text-slate-500">
          A short, curated list from the latest scan. Only setups clearing the quality bar appear:
          a Buy or Sell verdict with confidence of 60% or higher.
        </p>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <span className="text-xs text-slate-500">
            {data?.computedAt ? `Calls as of ${data.computedAt.replace('T', ' ').slice(0, 16)}` : 'Calls load from the latest scan'}
          </span>
          <button onClick={refresh} disabled={refreshing} className="btn-pill">
            {refreshing ? 'Refreshing…' : 'Refresh calls'}
          </button>
          {refreshError && <span className="text-xs text-rose-300">{refreshError}</span>}
        </div>
      </div>

      <Reveal><section className="space-y-3">
        <SectionTitle>Buy calls ({buys.length})</SectionTitle>
        {buys.length === 0 ? (
          <p className="text-sm text-slate-500">No buy setups clear the quality bar right now.</p>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {buys.map((c) => <CallCard key={c.symbol} call={c} side="buy" />)}
          </div>
        )}
      </section></Reveal>

      <Reveal><section className="space-y-3">
        <SectionTitle>Sell calls ({sells.length})</SectionTitle>
        {sells.length === 0 ? (
          <p className="text-sm text-slate-500">No sell setups clear the quality bar right now.</p>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {sells.map((c) => <CallCard key={c.symbol} call={c} side="sell" />)}
          </div>
        )}
      </section></Reveal>

      <p className="text-[11px] leading-relaxed text-slate-500">
        Calls are technical signals from the TrendWise engine, not investment advice. Entry zones, stops and
        targets are computed from price structure and volatility; always do your own research before trading.
      </p>
    </div>
  );
}
