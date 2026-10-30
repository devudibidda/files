import { useState } from 'react';
import { api, fmt } from '../api';
import { ChangePct, ErrorNote, Reveal, SectionTitle, Skeleton } from '../components/ui';
import { useFetch } from '../hooks';

const CATEGORIES = [
  ['flexi-cap', 'Flexi Cap'],
  ['large-cap', 'Large Cap'],
  ['mid-cap', 'Mid Cap'],
  ['small-cap', 'Small Cap'],
  ['elss', 'ELSS / Tax Saver'],
  ['index', 'Index'],
  ['liquid', 'Liquid'],
];

function FundDetail({ code, onClose }) {
  const { data, error, loading } = useFetch(() => api.mfDetail(code), [code]);
  if (loading) return <Skeleton className="h-64" />;
  if (error) return <ErrorNote error={error} />;
  if (!data) return null;
  const horizons = Object.entries(data.returns || {});
  return (
    <div className="card-pad card-hover">
      <div className="flex items-start justify-between gap-4">
        <div>
          <SectionTitle>{data.schemeName}</SectionTitle>
          <p className="mt-1 text-sm text-slate-500">
            {data.fundHouse} {data.category ? `· ${data.category}` : ''} {data.type ? `· ${data.type}` : ''}
          </p>
        </div>
        <button onClick={onClose} className="btn-pill shrink-0">Close</button>
      </div>
      <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm">
        <span className="text-slate-500">
          Latest NAV <span className="num font-semibold text-slate-200">{fmt.price(data.latestNav)}</span>
          <span className="text-slate-500"> ({data.navDate})</span>
        </span>
        <span className="text-slate-500">
          Volatility <span className="num font-semibold text-slate-200">{data.volatilityPct != null ? `${data.volatilityPct}% / yr` : '—'}</span>
        </span>
        <span className="text-slate-500">
          Max drawdown <span className="num font-semibold text-bear">{data.maxDrawdownPct != null ? `${data.maxDrawdownPct}%` : '—'}</span>
        </span>
      </div>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[480px]">
          <thead>
            <tr>
              <th className="table-head">Period</th>
              <th className="table-head text-right">Return</th>
              <th className="table-head text-right">CAGR</th>
            </tr>
          </thead>
          <tbody>
            {horizons.map(([label, v]) => (
              <tr key={label} className="hover:bg-ink-700/40 transition-colors">
                <td className="table-cell font-semibold text-slate-200">{label}</td>
                <td className="table-cell num text-right"><ChangePct value={v.returnPct} /></td>
                <td className="table-cell num text-right">{v.cagrPct != null ? `${v.cagrPct > 0 ? '+' : ''}${v.cagrPct}%` : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {Object.keys(data.sip || {}).length > 0 && (
        <>
          <div className="mt-5 mb-1 text-[11px] font-bold uppercase tracking-wide text-slate-500">
            Monthly SIP of ₹10,000 (illustration)
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[480px]">
              <thead>
                <tr>
                  <th className="table-head">Period</th>
                  <th className="table-head text-right">Invested</th>
                  <th className="table-head text-right">Value now</th>
                  <th className="table-head text-right">Gain</th>
                  <th className="table-head text-right">Annualized</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(data.sip).map(([label, v]) => (
                  <tr key={label} className="hover:bg-ink-700/40 transition-colors">
                    <td className="table-cell font-semibold text-slate-200">{label}</td>
                    <td className="table-cell num text-right text-slate-400">{fmt.price(v.invested)}</td>
                    <td className="table-cell num text-right text-slate-200">{fmt.price(v.value)}</td>
                    <td className="table-cell num text-right"><ChangePct value={v.gainPct} /></td>
                    <td className="table-cell num text-right text-slate-400">{v.annualizedPct != null ? `${v.annualizedPct > 0 ? '+' : ''}${v.annualizedPct}%` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-2 text-[11px] leading-relaxed text-slate-500">
            SIP illustration invests ₹10,000 at each month-end NAV and values the accumulated units at the latest NAV.
          </p>
        </>
      )}
      <p className="mt-3 text-[11px] leading-relaxed text-slate-500">{data.disclaimer}</p>
    </div>
  );
}

export default function MutualFundsPage() {
  const [category, setCategory] = useState('flexi-cap');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [selected, setSelected] = useState(null);

  const leaders = useFetch(() => api.mfLeaders(category), [category]);

  const runSearch = () => {
    const q = query.trim();
    if (!q) return;
    setSearching(true);
    api.mfSearch(q)
      .then((d) => setResults(d.results || []))
      .catch(() => setResults([]))
      .finally(() => setSearching(false));
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-display text-xl font-extrabold tracking-tight text-white">Mutual funds</h1>
        <p className="mt-1 text-sm text-slate-500">
          Funds are analyzed from NAV history — trailing returns, volatility, drawdown and SIP illustration.
          Unlike stocks and ETFs, funds get no intraday indicators: NAV updates once a day, so candle
          signals would be meaningless here.
        </p>
      </div>

      <Reveal><div className="card-pad card-hover">
        <SectionTitle>Find a fund</SectionTitle>
        <div className="flex gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && runSearch()}
            placeholder="Search by fund name — e.g. Parag Parikh Flexi Cap"
            className="w-full rounded-xl border border-white/10 bg-ink-800 px-3 py-2 text-sm text-white outline-none focus:border-brand-500"
          />
          <button onClick={runSearch} className="btn-pill btn-pill-active shrink-0">Search</button>
        </div>
        {searching && <p className="mt-3 text-sm text-slate-500">Searching…</p>}
        {results && (
          <div className="mt-3 divide-y divide-ink-700">
            {results.length === 0 && <p className="py-3 text-sm text-slate-500">No funds matched that name.</p>}
            {results.map((r) => (
              <button
                key={r.schemeCode}
                onClick={() => setSelected(r.schemeCode)}
                className="block w-full py-2 text-left text-sm text-slate-300 hover:text-white"
              >
                {r.schemeName} <span className="num text-xs text-slate-500">({r.schemeCode})</span>
              </button>
            ))}
          </div>
        )}
      </div></Reveal>

      {selected && (
        <Reveal>
          <FundDetail code={selected} onClose={() => setSelected(null)} />
        </Reveal>
      )}

      <Reveal><div className="card-pad card-hover">
        <SectionTitle>Top funds by category (past returns)</SectionTitle>
        <div className="mb-4 flex flex-wrap gap-1">
          {CATEGORIES.map(([id, label]) => (
            <button key={id} onClick={() => setCategory(id)} className={`btn-pill ${category === id ? 'btn-pill-active' : ''}`}>
              {label}
            </button>
          ))}
        </div>
        {leaders.loading ? (
          <Skeleton className="h-40" />
        ) : leaders.error ? (
          <ErrorNote error={leaders.error} retry={leaders.retry} />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px]">
                <thead>
                  <tr>
                    <th className="table-head">Fund</th>
                    <th className="table-head text-right">1Y return</th>
                    <th className="table-head text-right">3Y CAGR</th>
                    <th className="table-head text-right">Volatility</th>
                  </tr>
                </thead>
                <tbody>
                  {(leaders.data?.leaders || []).map((r) => (
                    <tr key={r.schemeCode} className="hover:bg-ink-700/40 transition-colors">
                      <td className="table-cell">
                        <button onClick={() => setSelected(r.schemeCode)} className="text-left font-semibold text-slate-200 hover:text-white">
                          {r.schemeName}
                        </button>
                        <div className="text-xs text-slate-500">{r.fundHouse}</div>
                      </td>
                      <td className="table-cell num text-right"><ChangePct value={r.return1Y} /></td>
                      <td className="table-cell num text-right"><ChangePct value={r.cagr3Y} /></td>
                      <td className="table-cell num text-right text-slate-400">{r.volatilityPct != null ? `${r.volatilityPct}%` : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {(leaders.data?.leaders || []).length === 0 && (
                <p className="py-10 text-center text-sm text-slate-500">No funds with fresh NAVs found in this category.</p>
              )}
            </div>
            <p className="mt-3 text-[11px] leading-relaxed text-slate-500">{leaders.data?.method}</p>
          </>
        )}
      </div></Reveal>
    </div>
  );
}
