import { useState } from 'react';
import { api, fmt } from '../api';
import { ErrorNote, Reveal, SectionTitle, Skeleton, VerdictBadge } from '../components/ui';

const QUESTIONS = [
  {
    id: 'horizon',
    title: 'When will you need this money?',
    options: [
      ['short', 'Within 3 years'],
      ['medium', 'In 3–5 years'],
      ['long', 'After 5 years'],
    ],
  },
  {
    id: 'reaction',
    title: 'If your ₹1,00,000 became ₹85,000 for a few months, what would you do?',
    options: [
      ['panic', "I'd sell - I can't watch it fall"],
      ['hold', "I'd hold and wait it out"],
      ['invest', "I'd keep investing - falls are buying chances"],
    ],
  },
  {
    id: 'emergency',
    title: 'Do you already have 3–6 months of expenses saved separately?',
    options: [
      ['yes', 'Yes, my safety net is ready'],
      ['no', 'Not yet'],
    ],
  },
];

const EDUCATION = [
  'Start a monthly SIP, even a small one, don\'t wait for the "right time" to enter.',
  'Equity money is money you won\'t need for years. Review once a year, not daily.',
  "Don't chase last year's winner - today's top-ranked fund is often tomorrow's average one.",
  'Never stop the SIP because markets fell, that\'s when the same money buys more units.',
];

function PickCard({ pick, monthly }) {
  const isMf = pick.kind === 'mf';
  const sipShare = Math.round((monthly * pick.allocationPct) / 100);
  return (
    <Reveal>
      <div className="card-pad card-hover">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="text-base font-semibold leading-snug text-slate-100">{pick.name}</div>
            <p className="mt-1 text-xs text-slate-500">
              {isMf ? (
                <>{pick.fundHouse} · {pick.category} · Direct Growth{ pick.navDate ? ` · NAV ${pick.navDate}` : ''}</>
              ) : (
                <>{pick.symbol} · ETF</>
              )}
            </p>
            <p className="mt-1 text-xs font-medium text-violet-300">{pick.job}</p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-gradient num">{pick.allocationPct}%</div>
            <div className="text-xs text-slate-500">of every ₹100</div>
            <div className="mt-1 text-sm font-semibold text-slate-200 num">₹{fmt.num(sipShare)} / month</div>
          </div>
        </div>

        <div className="mt-3 h-2 overflow-hidden rounded-full bg-ink-700/70">
          <div
            className="h-full rounded-full bg-gradient-to-r from-violet-500 via-fuchsia-400 to-amber-300"
            style={{ width: `${pick.allocationPct}%` }}
          />
        </div>

        <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1.5 text-xs text-slate-400">
          {isMf ? (
            <>
              <span>3Y CAGR <b className="text-slate-200 num">{pick.cagr3Y != null ? `${pick.cagr3Y}%` : '-'}</b></span>
              <span>1Y <b className="text-slate-200 num">{pick.return1Y != null ? `${pick.return1Y}%` : '-'}</b></span>
              <span>Volatility <b className="text-slate-200 num">{pick.volatilityPct != null ? `${pick.volatilityPct}% / yr` : '-'}</b></span>
              <span>Max drawdown <b className="text-bear num">{pick.maxDrawdownPct != null ? `${pick.maxDrawdownPct}%` : '-'}</b></span>
            </>
          ) : (
            <>
              {pick.ratingNote ? (
                <span className="text-amber-200">{pick.ratingNote}</span>
              ) : (
                <span>Trend score <b className="text-slate-200 num">{pick.score != null ? pick.score.toFixed(1) : '-'}</b></span>
              )}
              {pick.verdict && <VerdictBadge verdict={pick.verdict} />}
            </>
          )}
        </div>

        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <div className="mb-1.5 text-[11px] font-bold uppercase tracking-wide text-bull">Pros</div>
            <ul className="space-y-1.5 text-sm leading-snug text-slate-300">
              {pick.pros.map((p, i) => <li key={i}>✓ {p}</li>)}
            </ul>
          </div>
          <div>
            <div className="mb-1.5 text-[11px] font-bold uppercase tracking-wide text-bear">Cons</div>
            <ul className="space-y-1.5 text-sm leading-snug text-slate-300">
              {pick.cons.map((c, i) => <li key={i}>✗ {c}</li>)}
            </ul>
          </div>
        </div>
        <p className="mt-3 text-xs leading-relaxed text-slate-500">How it was picked: {pick.selectionNote}</p>
      </div>
    </Reveal>
  );
}

export default function FinderPage() {
  const [answers, setAnswers] = useState({});
  const [monthly, setMonthly] = useState(5000);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [started, setStarted] = useState(false);

  const ready = QUESTIONS.every((q) => answers[q.id]);

  async function build() {
    setLoading(true);
    setError(null);
    setStarted(true);
    try {
      const res = await api.advisorPortfolio(answers.horizon, answers.reaction);
      setData(res);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setAnswers({});
    setData(null);
    setError(null);
    setStarted(false);
  }

  return (
    <div className="space-y-6">
      <Reveal>
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            My <span className="text-gradient">First Portfolio</span>
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
            Three quick questions, then a starter mix of ETFs and mutual funds with a percentage
            for each, plus honest pros and cons. Built for someone investing for the first time.
          </p>
        </div>
      </Reveal>

      {!data && (
        <Reveal>
          <div className="card-pad space-y-6">
            {QUESTIONS.map((q) => (
              <div key={q.id}>
                <div className="mb-2 font-semibold text-slate-200">{q.title}</div>
                <div className="flex flex-wrap gap-2">
                  {q.options.map(([value, label]) => (
                    <button
                      key={value}
                      onClick={() => setAnswers((a) => ({ ...a, [q.id]: value }))}
                      className={answers[q.id] === value ? 'btn-pill-active' : 'btn-pill'}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            ))}
            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={build}
                disabled={!ready || loading}
                className="glass-btn disabled:cursor-not-allowed disabled:opacity-40"
              >
                {loading ? 'Building your portfolio…' : 'See my starter portfolio'}
              </button>
              {loading && (
                <span className="text-xs text-slate-500">
                  First build can take up to a minute while fund data loads.
                </span>
              )}
            </div>
            {started && error && <ErrorNote error={error} retry={build} />}
          </div>
        </Reveal>
      )}

      {data && (
        <>
          <Reveal>
            <div className="card-pad">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <SectionTitle>Your profile: {data.profileLabel}</SectionTitle>
                  <p className="mt-1 max-w-2xl text-sm leading-relaxed text-slate-400">{data.profileLine}</p>
                  <p className="mt-3 rounded-xl border border-violet-400/25 bg-violet-400/10 px-4 py-2.5 text-sm text-violet-100">
                    {data.keySentence}
                  </p>
                </div>
                <button onClick={reset} className="btn-pill shrink-0">Start over</button>
              </div>

              {answers.emergency === 'no' && (
                <div className="mt-4 rounded-xl border border-amber-400/30 bg-amber-400/10 px-4 py-3 text-sm leading-relaxed text-amber-100">
                  <b>Before you invest a rupee:</b> set aside 3–6 months of expenses somewhere safe
                  (a liquid fund works). The mix below is for <i>after</i> that safety net is ready,
                  equity money is money you won't need for years.
                </div>
              )}

              <div className="mt-4 flex flex-wrap items-center gap-2 text-sm text-slate-300">
                <span>If I invest</span>
                <span className="text-slate-500">₹</span>
                <input
                  type="number"
                  min={500}
                  step={500}
                  value={monthly}
                  onChange={(e) => setMonthly(Number(e.target.value) || 0)}
                  className="w-28 rounded-lg border border-white/10 bg-ink-800 px-3 py-1.5 text-sm text-slate-100 outline-none focus:border-violet-400/60"
                />
                <span>every month, that's how much goes to each pick:</span>
              </div>
            </div>
          </Reveal>

          {data.incomplete && (
            <div className="rounded-xl border border-amber-400/30 bg-amber-400/10 px-4 py-3 text-sm text-amber-100">
              {data.incompleteNote}
            </div>
          )}

          <div className="grid gap-4 lg:grid-cols-2">
            {data.picks.map((pick) => (
              <PickCard key={pick.role} pick={pick} monthly={monthly} />
            ))}
          </div>

          <Reveal>
            <div className="card-pad space-y-3 text-sm leading-relaxed text-slate-400">
              <div>
                <b className="text-slate-200">How the picks were chosen. </b>
                {data.method}
              </div>
              <div>
                <b className="text-slate-200">Coverage. </b>
                {data.coverageNote}
              </div>
              <div>
                <b className="text-slate-200">What this doesn't show. </b>
                {data.missingDataNote}
              </div>
              <div>
                <b className="text-slate-200">Good habits. </b>
                <ul className="mt-1.5 space-y-1">
                  {EDUCATION.map((line, i) => <li key={i}>• {line}</li>)}
                </ul>
              </div>
              <div className="rounded-xl border border-white/10 bg-ink-800/60 px-4 py-3 text-xs leading-relaxed text-slate-500">
                {data.disclaimer}
              </div>
            </div>
          </Reveal>
        </>
      )}

      {loading && !data && <Skeleton className="h-64" />}
    </div>
  );
}
