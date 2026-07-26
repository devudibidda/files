import { fmt } from '../api';
import { SentimentChip } from './ui';

export default function NewsList({ items, compact = false }) {
  if (!items?.length) {
    return <p className="py-6 text-center text-sm text-slate-500">No recent headlines found.</p>;
  }
  return (
    <ul className="divide-y divide-ink-700">
      {items.map((n, i) => (
        <li key={i} className="flex items-start gap-3 py-3">
          <div className="min-w-0 flex-1">
            {n.link ? (
              <a
                href={n.link}
                target="_blank"
                rel="noreferrer"
                className={`block font-medium text-slate-200 hover:text-brand-400 transition-colors ${compact ? 'text-[13px] leading-snug' : 'text-sm'}`}
              >
                {n.title}
              </a>
            ) : (
              <span className={`block font-medium text-slate-200 ${compact ? 'text-[13px] leading-snug' : 'text-sm'}`}>{n.title}</span>
            )}
            <div className="mt-1 flex items-center gap-2 text-[11px] text-slate-500">
              <span>{n.source}</span>
              {n.publishedAt && (
                <>
                  <span>·</span>
                  <span>{fmt.timeAgo(n.publishedAt)}</span>
                </>
              )}
            </div>
          </div>
          <SentimentChip label={n.sentimentLabel} />
        </li>
      ))}
    </ul>
  );
}
