import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { api, clientId, fmt } from '../api';
import NewsList from '../components/NewsList';
import PriceChart from '../components/PriceChart';
import VerdictGauge from '../components/VerdictGauge';
import { ChangePct, DemoBanner, ErrorNote, SectionTitle, SentimentChip, Skeleton, VerdictBadge } from '../components/ui';
import { useFetch } from '../hooks';

const RANGES = ['1mo', '3mo', '6mo', '1y', '2y'];

function Header({ quote, analysis, onWatch, watched }) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-extrabold tracking-tight text-white">{quote.symbol}</h1>
          <VerdictBadge verdict={analysis?.verdict} />
          <button
            onClick={onWatch}
            title={watched ? 'Remove from watchlist' : 'Add to watchlist'}
            className={`text-xl leading-none transition-colors ${watched ? 'text-amber-300' : 'text-slate-600 hover:text-amber-300'}`}
          >
            ★
          </button>
        </div>
        <p className="mt-0.5 text-sm text-slate-500">
          {quote.name} {quote.sector ? `· ${quote.sector}` : ''} {quote.type === 'etf' ? '· ETF' : ''}
        </p>
      </div>
      <div className="text-right">
        <div className="num text-3xl font-extrabold text-white">{fmt.price(quote.price)}</div>
        <div className="mt-0.5 flex items-center justify-end gap-2 text-sm">
          <ChangePct value={quote.changePct} />
          <span className="num text-slate-500">({quote.change > 0 ? '+' : ''}{quote.change})</span>
        </div>
      </div>
    </div>
  );
}

function TradePlanCard({ plan, verdict }) {
  if (!plan) return null;
  const actionLabel = {
    BUY: 'Buy',
    BUY_ON_DIP: 'Buy on dip',
    WAIT: 'Wait / range-trade',
    AVOID_OR_EXIT: 'Avoid fresh longs',
  }[plan.action] || plan.action;

  const row = (label, value, cls = 'text-slate-200') =>
    value != null && (
      <div className="flex items-center justify-between py-1.5">
        <span className="text-xs text-slate-500">{label}</span>
        <span className={`num text-sm font-semibold ${cls}`}>{value}</span>
      </div>
    );

  return (
    <div className="card-pad">
      <SectionTitle right={<VerdictBadge verdict={verdict} />}>Trade plan</SectionTitle>
      <div className="mb-3 rounded-xl bg-ink-700/60 px-3 py-2 text-center text-sm font-bold tracking-wide text-white">
        {actionLabel}
      </div>
      <div className="divide-y divide-ink-700">
        {row('Entry zone', plan.entryZone ? `${fmt.price(plan.entryZone[0])} – ${fmt.price(plan.entryZone[1])}` : null)}
        {row('Stop-loss', plan.stopLoss != null ? fmt.price(plan.stopLoss) : null, 'text-bear')}
        {row('Target 1 (1.5R)', plan.target1 != null ? fmt.price(plan.target1) : null, 'text-bull')}
        {row('Target 2 (2.5R)', plan.target2 != null ? fmt.price(plan.target2) : null, 'text-bull')}
        {row('Risk : Reward', plan.riskReward != null ? `1 : ${plan.riskReward}` : null)}
      </div>
      {plan.notes?.length > 0 && (
        <ul className="mt-3 space-y-1.5">
          {plan.notes.map((n, i) => (
            <li key={i} className="text-xs leading-relaxed text-slate-400">
              • {n}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function IndicatorTable({ votes }) {
  const stateStyles = {
    bullish: 'text-bull bg-bull/10',
    bearish: 'text-bear bg-bear/10',
    neutral: 'text-slate-400 bg-ink-700',
  };
  return (
    <div className="card overflow-hidden">
      <div className="px-5 pt-4">
        <SectionTitle>Indicator breakdown</SectionTitle>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px]">
          <thead>
            <tr>
              <th className="table-head">Indicator</th>
              <th className="table-head">Value</th>
              <th className="table-head">Signal</th>
              <th className="table-head">Why</th>
            </tr>
          </thead>
          <tbody>
            {votes.map((v) => (
              <tr key={v.indicator} className="hover:bg-ink-700/40 transition-colors">
                <td className="table-cell whitespace-nowrap font-semibold text-slate-200">{v.indicator}</td>
                <td className="table-cell num text-slate-400">{v.value}</td>
                <td className="table-cell">
                  <span className={`chip ${stateStyles[v.state]}`}>{v.state}</span>
                </td>
                <td className="table-cell text-xs leading-relaxed text-slate-400">{v.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function LevelsCard({ levels, pivots, price }) {
  const Zone = ({ z, kind }) => (
    <div className="flex items-center justify-between py-1">
      <span className={`num text-sm font-semibold ${kind === 's' ? 'text-bull' : 'text-bear'}`}>{fmt.price(z.level)}</span>
      <span className="text-[11px] text-slate-500">{z.strength} touch{z.strength > 1 ? 'es' : ''}</span>
    </div>
  );
  return (
    <div className="card-pad">
      <SectionTitle>Key levels</SectionTitle>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="mb-1 text-[11px] font-bold uppercase tracking-wide text-bear">Resistance</div>
          {levels.resistances.length ? levels.resistances.map((z, i) => <Zone key={i} z={z} kind="r" />) : <p className="text-xs text-slate-600">None nearby</p>}
        </div>
        <div>
          <div className="mb-1 text-[11px] font-bold uppercase tracking-wide text-bull">Support</div>
          {levels.supports.length ? levels.supports.map((z, i) => <Zone key={i} z={z} kind="s" />) : <p className="text-xs text-slate-600">None nearby</p>}
        </div>
      </div>
      <div className="mt-4 border-t border-ink-700 pt-3">
        <div className="mb-1 text-[11px] font-bold uppercase tracking-wide text-slate-500">Daily pivots</div>
        <div className="grid grid-cols-4 gap-2 text-center">
          {['s2', 's1', 'pivot', 'r1'].map((k) => (
            <div key={k} className="rounded-lg bg-ink-700/60 px-1 py-1.5">
              <div className="text-[10px] uppercase text-slate-500">{k}</div>
              <div className="num text-xs font-semibold text-slate-200">{pivots[k]}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function StockPage() {
  const { symbol } = useParams();
  const [range, setRange] = useState('1y');
  const [tab, setTab] = useState('technicals');

  const quote = useFetch(() => api.quote(symbol), [symbol]);
  const analysis = useFetch(() => api.analysis(symbol), [symbol]);
  const history = useFetch(() => api.history(symbol, range), [symbol, range]);
  const news = useFetch(() => api.stockNews(symbol), [symbol]);

  const [watched, setWatched] = useState(() => (localStorage.getItem('tw-watchlist') || '').split(',').includes(symbol.toUpperCase()));
  const toggleWatch = () => {
    const id = clientId();
    const sym = symbol.toUpperCase();
    const list = (localStorage.getItem('tw-watchlist') || '').split(',').filter(Boolean);
    const next = list.includes(sym) ? list.filter((s) => s !== sym) : [...list, sym];
    localStorage.setItem('tw-watchlist', next.join(','));
    setWatched(next.includes(sym));
    (list.includes(sym) ? api.watchlist.remove(id, sym) : api.watchlist.add(id, sym)).catch(() => {});
  };

  if (quote.loading) return <Skeleton className="h-96" />;
  if (quote.error) return <ErrorNote error={quote.error} retry={quote.retry} />;

  const a = analysis.data;

  return (
    <div className="space-y-5">
      <DemoBanner source={quote.data.source} />
      <Header quote={quote.data} analysis={a} onWatch={toggleWatch} watched={watched} />

      <div className="grid gap-4 xl:grid-cols-3">
        {/* chart column */}
        <div className="card-pad xl:col-span-2">
          <div className="mb-3 flex items-center gap-1">
            {RANGES.map((r) => (
              <button key={r} onClick={() => setRange(r)} className={`btn-pill ${range === r ? 'btn-pill-active' : ''}`}>
                {r.toUpperCase()}
              </button>
            ))}
          </div>
          {history.loading ? (
            <Skeleton className="h-[560px]" />
          ) : history.error ? (
            <ErrorNote error={history.error} retry={history.retry} />
          ) : (
            <PriceChart candles={history.data.candles} overlays={history.data.overlays} />
          )}
        </div>

        {/* analysis column */}
        <div className="space-y-4">
          <div className="card-pad">
            <SectionTitle>Composite verdict</SectionTitle>
            {analysis.loading ? (
              <Skeleton className="h-52" />
            ) : analysis.error ? (
              <ErrorNote error={analysis.error} retry={analysis.retry} />
            ) : (
              <>
                <VerdictGauge score={a.score} verdict={a.verdict} confidence={a.confidence} />
                <p className="mt-3 border-t border-ink-700 pt-3 text-xs leading-relaxed text-slate-400">{a.summary}</p>
                <div className="mt-3 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">Weekly timeframe</span>
                    <SentimentChip label={{ bullish: 'positive', bearish: 'negative' }[a.weeklyTrend.state] || 'neutral'} />
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">News sentiment ({a.newsSentiment.count} headlines)</span>
                    <span className="flex items-center gap-1.5">
                      <SentimentChip label={a.newsSentiment.label} />
                      <span className="num text-slate-400">
                        {a.newsSentiment.scoreAdjustment > 0 ? '+' : ''}
                        {a.newsSentiment.scoreAdjustment} pts
                      </span>
                    </span>
                  </div>
                </div>
              </>
            )}
          </div>
          {a && <TradePlanCard plan={a.tradePlan} verdict={a.verdict} />}
        </div>
      </div>

      {/* tabs */}
      <div>
        <div className="mb-4 flex gap-1 border-b border-ink-700">
          {[
            ['technicals', 'Technical breakdown'],
            ['levels', 'Levels & stats'],
            ['news', 'News'],
          ].map(([id, label]) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`px-4 py-2.5 text-sm font-semibold transition-colors ${
                tab === id ? 'border-b-2 border-brand-500 text-white' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {tab === 'technicals' && (a ? <IndicatorTable votes={a.votes} /> : <Skeleton className="h-64" />)}

        {tab === 'levels' && a && (
          <div className="grid gap-4 md:grid-cols-2">
            <LevelsCard levels={a.levels} pivots={a.pivots} price={a.price} />
            <div className="card-pad">
              <SectionTitle>52-week stats</SectionTitle>
              <div className="divide-y divide-ink-700">
                {[
                  ['52-week high', fmt.price(a.stats.high52w)],
                  ['52-week low', fmt.price(a.stats.low52w)],
                  ['From 52w high', fmt.pct(a.stats.distFromHigh52wPct)],
                  ['From 52w low', fmt.pct(a.stats.distFromLow52wPct)],
                  ['ATR (volatility)', a.stats.atrPct != null ? `${a.stats.atrPct}% / day` : '—'],
                ].map(([label, value]) => (
                  <div key={label} className="flex items-center justify-between py-2">
                    <span className="text-xs text-slate-500">{label}</span>
                    <span className="num text-sm font-semibold text-slate-200">{value}</span>
                  </div>
                ))}
              </div>
              <p className="mt-4 text-xs leading-relaxed text-slate-500">{a.weeklyTrend.reason}</p>
            </div>
          </div>
        )}

        {tab === 'news' && (
          <div className="card-pad">
            {news.loading ? <Skeleton className="h-40" /> : <NewsList items={news.data?.items} />}
          </div>
        )}
      </div>
    </div>
  );
}
