import { useState } from 'react';
import { api } from '../api';
import { fmt } from '../api';
import { ChangePct, ErrorNote, Reveal, SectionTitle, Skeleton, SymbolLink, VerdictBadge } from '../components/ui';
import { useFetch } from '../hooks';

function ScoreBar({ score }) {
  const pct = Math.min(100, Math.abs(score));
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-ink-700">
        <div className={`h-full ${score >= 0 ? 'bg-bull' : 'bg-bear'}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`num text-xs font-bold ${score >= 0 ? 'text-bull' : 'text-bear'}`}>
        {score > 0 ? `+${score}` : score}
      </span>
    </div>
  );
}

export default function ScreenerPage() {
  const [scan, setScan] = useState('strong_buy');
  const [type, setType] = useState(null);

  const scans = useFetch(() => api.scans(), []);
  const { data, error, loading, retry } = useFetch(() => api.screener(scan, type), [scan, type]);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-extrabold tracking-tight text-white">Screener</h1>
        <p className="mt-1 text-sm text-slate-500">Signal scans across the tracked NSE universe, refreshed every few minutes.</p>
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        {(scans.data?.scans || []).map((s) => (
          <button
            key={s.id}
            onClick={() => setScan(s.id)}
            className={`rounded-full px-3.5 py-1.5 text-xs font-semibold transition-colors ${
              scan === s.id ? 'bg-brand-500/20 text-brand-400 ring-1 ring-brand-500/40' : 'bg-ink-800 text-slate-400 hover:text-slate-200 ring-1 ring-ink-600'
            }`}
          >
            {s.label}
          </button>
        ))}
        <div className="ml-auto flex gap-1">
          {[
            [null, 'All'],
            ['equity', 'Stocks'],
            ['etf', 'ETFs'],
          ].map(([t, label]) => (
            <button key={label} onClick={() => setType(t)} className={`btn-pill ${type === t ? 'btn-pill-active' : ''}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <Skeleton className="h-96" />
      ) : error ? (
        <ErrorNote error={error} retry={retry} />
      ) : (
        <Reveal>
        <div className="card card-hover overflow-hidden">
          <div className="flex items-center justify-between px-5 pt-4">
            <SectionTitle>{data.label}</SectionTitle>
            <span className="text-xs text-slate-500">{data.results.length} matches</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px]">
              <thead>
                <tr>
                  <th className="table-head">Symbol</th>
                  <th className="table-head">Sector</th>
                  <th className="table-head text-right">Price</th>
                  <th className="table-head">Score</th>
                  <th className="table-head">Verdict</th>
                  <th className="table-head text-right">RSI</th>
                  <th className="table-head text-right">ADX</th>
                  <th className="table-head">Supertrend</th>
                  <th className="table-head text-right">vs 52w high</th>
                </tr>
              </thead>
              <tbody>
                {data.results.map((r) => (
                  <tr key={r.symbol} className="hover:bg-ink-700/40 transition-colors">
                    <td className="table-cell">
                      <SymbolLink symbol={r.symbol} name={r.name} />
                    </td>
                    <td className="table-cell text-xs text-slate-500">{r.type === 'etf' ? 'ETF' : r.sector}</td>
                    <td className="table-cell num text-right text-slate-200">{fmt.price(r.price)}</td>
                    <td className="table-cell">
                      <ScoreBar score={r.score} />
                    </td>
                    <td className="table-cell">
                      <VerdictBadge verdict={r.verdict} />
                    </td>
                    <td className="table-cell num text-right text-slate-300">{r.rsi?.toFixed(0) ?? '—'}</td>
                    <td className="table-cell num text-right text-slate-300">{r.adx?.toFixed(0) ?? '—'}</td>
                    <td className="table-cell">
                      <span className={`text-xs font-semibold ${r.supertrend === 'bullish' ? 'text-bull' : 'text-bear'}`}>
                        {r.supertrend}
                      </span>
                    </td>
                    <td className="table-cell text-right">
                      <ChangePct value={r.distFromHigh52wPct} className="text-xs" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data.results.length === 0 && <p className="py-10 text-center text-sm text-slate-500">No symbols match this scan right now.</p>}
          </div>
        </div></Reveal>
      )}
    </div>
  );
}
