import { VerdictBadge } from './ui';

/**
 * Semi-circular score gauge: -100 (Strong Sell) .. +100 (Strong Buy).
 */
export default function VerdictGauge({ score = 0, verdict, confidence }) {
  const clamped = Math.max(-100, Math.min(100, score));
  // map score to angle: -100 → 180°, +100 → 0° (SVG arc from left to right)
  const t = (clamped + 100) / 200; // 0..1
  const angle = Math.PI * (1 - t);
  const cx = 100, cy = 95, r = 78;
  const needleX = cx + r * 0.82 * Math.cos(angle);
  const needleY = cy - r * 0.82 * Math.sin(angle);

  const arc = (from, to, color, width = 10) => {
    const a1 = Math.PI * (1 - from);
    const a2 = Math.PI * (1 - to);
    const x1 = cx + r * Math.cos(a1);
    const y1 = cy - r * Math.sin(a1);
    const x2 = cx + r * Math.cos(a2);
    const y2 = cy - r * Math.sin(a2);
    return <path d={`M ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2}`} stroke={color} strokeWidth={width} fill="none" strokeLinecap="round" />;
  };

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 200 110" className="w-full max-w-[260px]">
        {arc(0.0, 0.19, '#F43F5E')}
        {arc(0.21, 0.39, '#FB7185')}
        {arc(0.41, 0.59, '#FBBF24')}
        {arc(0.61, 0.79, '#34D399')}
        {arc(0.81, 1.0, '#10B981')}
        <line x1={cx} y1={cy} x2={needleX} y2={needleY} stroke="#E2E8F0" strokeWidth="3" strokeLinecap="round" />
        <circle cx={cx} cy={cy} r="6" fill="#E2E8F0" />
        <text x="14" y="108" fontSize="9" fill="#64748B">STRONG SELL</text>
        <text x="152" y="108" fontSize="9" fill="#64748B">STRONG BUY</text>
      </svg>
      <div className="-mt-2 text-center">
        <div className="num text-3xl font-extrabold text-white">{score > 0 ? `+${score}` : score}</div>
        <div className="mt-1.5">
          <VerdictBadge verdict={verdict} className="text-sm px-3 py-1" />
        </div>
        {confidence != null && (
          <div className="mt-2 text-xs text-slate-500">
            Signal agreement <span className="num font-semibold text-slate-300">{confidence}%</span>
          </div>
        )}
      </div>
    </div>
  );
}
