import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, clientId, fmt } from '../api';
import { ChangePct, Reveal, SectionTitle, Skeleton, SymbolLink, VerdictBadge } from '../components/ui';

function localList() {
  return (localStorage.getItem('tw-watchlist') || '').split(',').filter(Boolean);
}

export default function WatchlistPage() {
  const [symbols, setSymbols] = useState(localList());
  const [rows, setRows] = useState({});
  const [loading, setLoading] = useState(false);

  // Merge with the server copy when available (survives browser changes)
  useEffect(() => {
    api.watchlist
      .get(clientId())
      .then((d) => {
        const server = d.symbols || [];
        const merged = [...new Set([...localList(), ...server])];
        localStorage.setItem('tw-watchlist', merged.join(','));
        setSymbols(merged);
      })
      .catch(() => {});
  }, []);

  const load = useCallback(async (syms) => {
    setLoading(true);
    const results = await Promise.allSettled(
      syms.map(async (s) => {
        const [quote, analysis] = await Promise.allSettled([api.quote(s), api.analysis(s)]);
        return {
          symbol: s,
          quote: quote.status === 'fulfilled' ? quote.value : null,
          analysis: analysis.status === 'fulfilled' ? analysis.value : null,
        };
      }),
    );
    const map = {};
    for (const r of results) if (r.status === 'fulfilled') map[r.value.symbol] = r.value;
    setRows(map);
    setLoading(false);
  }, []);

  useEffect(() => {
    if (symbols.length) load(symbols);
  }, [symbols, load]);

  const remove = (sym) => {
    const next = symbols.filter((s) => s !== sym);
    localStorage.setItem('tw-watchlist', next.join(','));
    setSymbols(next);
    api.watchlist.remove(clientId(), sym).catch(() => {});
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-display text-xl font-extrabold tracking-tight text-white">Watchlist</h1>
        <p className="mt-1 text-sm text-slate-500">
          Star any stock from its analysis page to track it here with a live verdict.
        </p>
      </div>

      {symbols.length === 0 ? (
        <Reveal><div className="card-pad card-hover py-16 text-center">
          <p className="text-4xl">★</p>
          <p className="mt-3 font-semibold text-slate-300">Your watchlist is empty</p>
          <p className="mt-1 text-sm text-slate-500">
            Search for a stock and tap the star on its page, or start from the{' '}
            <Link to="/screener" className="text-brand-400 hover:underline">
              screener
            </Link>
            .
          </p>
        </div></Reveal>
      ) : (
        <Reveal><div className="card card-hover overflow-hidden">
          <div className="px-5 pt-4">
            <SectionTitle>{symbols.length} tracked symbols</SectionTitle>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px]">
              <thead>
                <tr>
                  <th className="table-head">Symbol</th>
                  <th className="table-head text-right">Price</th>
                  <th className="table-head text-right">Change</th>
                  <th className="table-head text-right">Score</th>
                  <th className="table-head">Verdict</th>
                  <th className="table-head">Plan</th>
                  <th className="table-head" />
                </tr>
              </thead>
              <tbody>
                {symbols.map((s) => {
                  const r = rows[s];
                  const a = r?.analysis;
                  return (
                    <tr key={s} className="hover:bg-ink-700/40 transition-colors">
                      <td className="table-cell">
                        <SymbolLink symbol={s} name={a?.name} />
                      </td>
                      <td className="table-cell num text-right text-slate-200">
                        {loading && !r ? <Skeleton className="ml-auto h-4 w-16" /> : fmt.price(r?.quote?.price)}
                      </td>
                      <td className="table-cell text-right">
                        <ChangePct value={r?.quote?.changePct} className="text-xs" />
                      </td>
                      <td className="table-cell num text-right">
                        {a ? (
                          <span className={`font-bold ${a.score >= 0 ? 'text-bull' : 'text-bear'}`}>
                            {a.score > 0 ? `+${a.score}` : a.score}
                          </span>
                        ) : (
                          '-'
                        )}
                      </td>
                      <td className="table-cell">
                        <VerdictBadge verdict={a?.verdict} />
                      </td>
                      <td className="table-cell text-xs text-slate-400">
                        {a?.tradePlan?.action?.replaceAll('_', ' ').toLowerCase() ?? '-'}
                      </td>
                      <td className="table-cell text-right">
                        <button onClick={() => remove(s)} className="text-xs font-semibold text-slate-500 hover:text-bear transition-colors">
                          Remove
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div></Reveal>
      )}
    </div>
  );
}
