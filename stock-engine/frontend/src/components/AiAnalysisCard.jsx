import { useEffect, useRef, useState } from 'react';
import { api } from '../api';
import { ErrorNote, SectionTitle, Skeleton } from './ui';

// AI analysis section for the stock page. Generation runs on the server's
// local Ollama model and takes a minute or more on CPU, so the card polls
// until the cached result is ready instead of blocking the page.
export default function AiAnalysisCard({ symbol }) {
  const [state, setState] = useState({ status: 'loading' });
  const polls = useRef(0);
  const timer = useRef(null);

  const fetchStatus = async () => {
    try {
      const d = await api.aiAnalysis(symbol);
      setState(d);
      if (d.status === 'generating' && polls.current < 30) {
        polls.current += 1;
        timer.current = setTimeout(fetchStatus, 10000);
      } else if (d.status === 'generating') {
        setState({ ...d, status: 'timeout' });
      }
    } catch (e) {
      setState({ status: 'error', error: e });
    }
  };

  useEffect(() => {
    polls.current = 0;
    setState({ status: 'loading' });
    fetchStatus();
    return () => clearTimeout(timer.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol]);

  const generate = async () => {
    setState({ status: 'generating' });
    polls.current = 0;
    try {
      await api.refreshAiAnalysis(symbol);
      timer.current = setTimeout(fetchStatus, 10000);
    } catch (e) {
      setState({ status: 'error', error: e });
    }
  };

  const when = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    return Number.isNaN(d.getTime()) ? '' : d.toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' });
  };

  return (
    <div id="ai-analysis" className="card-pad card-hover">
      <SectionTitle
        right={
          state.model ? <span className="text-[11px] font-normal text-slate-500">Model: {state.model}</span> : null
        }
      >
        AI analysis
      </SectionTitle>

      {state.status === 'loading' && <Skeleton className="h-40" />}

      {state.status === 'error' && <ErrorNote error={state.error} retry={fetchStatus} />}

      {state.status === 'ready' && (
        <>
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-300">{state.text}</p>
          <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-ink-700 pt-3">
            <p className="text-[11px] leading-relaxed text-slate-500">
              Generated {when(state.computedAt)} from that day's price and technical verdict. Educational only, not investment advice.
            </p>
            <button onClick={generate} className="btn-pill shrink-0">
              Refresh
            </button>
          </div>
        </>
      )}

      {(state.status === 'missing' || state.status === 'timeout') && (
        <>
          {state.lastError && <p className="mb-3 text-xs leading-relaxed text-bear">{state.lastError}</p>}
          <p className="text-sm leading-relaxed text-slate-400">
            {state.status === 'timeout'
              ? 'Still generating after about 5 minutes. The server may be busy; try checking again.'
              : 'No AI analysis yet for this stock. Generation runs on the server and takes a couple of minutes.'}
          </p>
          <button onClick={generate} className="btn-pill mt-3">
            {state.status === 'timeout' ? 'Check again' : 'Generate AI analysis'}
          </button>
        </>
      )}

      {state.status === 'generating' && (
        <>
          <Skeleton className="h-40" />
          <p className="mt-3 text-xs leading-relaxed text-slate-500">
            Generating on the server with the local model. This usually takes a couple of minutes; the result is saved, so the next visit is instant.
          </p>
        </>
      )}
    </div>
  );
}
