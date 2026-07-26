import { api, fmt } from '../api';
import { ChangePct, ErrorNote, SectionTitle, Skeleton, SymbolLink, VerdictBadge } from '../components/ui';
import { useFetch } from '../hooks';

export default function EtfPage() {
  const { data, error, loading, retry } = useFetch(() => api.screener('all', 'etf'), []);

  if (loading) return <Skeleton className="h-96" />;
  if (error) return <ErrorNote error={error} retry={retry} />;

  const rows = data?.results || [];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-extrabold tracking-tight text-white">ETF hub</h1>
        <p className="mt-1 text-sm text-slate-500">
          Curated NSE-listed ETFs — index, gold, sector, factor and international — ranked by composite signal score.
        </p>
      </div>

      <div className="card overflow-hidden">
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
                  <td className="table-cell num text-right text-slate-300">{r.rsi?.toFixed(0) ?? '—'}</td>
                  <td className="table-cell text-right">
                    <ChangePct value={r.distFromHigh52wPct} className="text-xs" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {rows.length === 0 && <p className="py-10 text-center text-sm text-slate-500">ETF data is still loading on the server — try again shortly.</p>}
        </div>
      </div>
    </div>
  );
}
