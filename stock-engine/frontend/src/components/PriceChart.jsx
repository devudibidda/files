import {
  CandlestickSeries,
  createChart,
  HistogramSeries,
  LineSeries,
} from 'lightweight-charts';
import { useEffect, useRef, useState } from 'react';

const CHART_OPTS = {
  layout: {
    background: { color: 'transparent' },
    textColor: '#94A3B8',
    fontFamily: 'Inter, system-ui, sans-serif',
    panes: { separatorColor: '#1E2A44', separatorHoverColor: '#2C3B5C' },
  },
  grid: {
    vertLines: { color: 'rgba(30, 42, 68, 0.5)' },
    horzLines: { color: 'rgba(30, 42, 68, 0.5)' },
  },
  crosshair: {
    vertLine: { color: '#475569', labelBackgroundColor: '#1E2A44' },
    horzLine: { color: '#475569', labelBackgroundColor: '#1E2A44' },
  },
  rightPriceScale: { borderColor: '#1E2A44' },
  timeScale: { borderColor: '#1E2A44', rightOffset: 4 },
  autoSize: true,
};

const OVERLAY_DEFS = [
  { key: 'ema20', label: 'EMA 20', color: '#38BDF8' },
  { key: 'ema50', label: 'EMA 50', color: '#A78BFA' },
  { key: 'ema200', label: 'EMA 200', color: '#F59E0B' },
  { key: 'bb', label: 'Bollinger', color: '#64748B' },
  { key: 'supertrend', label: 'Supertrend', color: '#10B981' },
];

export default function PriceChart({ candles, overlays, height = 560 }) {
  const containerRef = useRef(null);
  const [enabled, setEnabled] = useState({ ema20: true, ema50: true, ema200: true, bb: false, supertrend: false });

  useEffect(() => {
    if (!containerRef.current || !candles?.length) return;

    const chart = createChart(containerRef.current, CHART_OPTS);

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#10B981',
      downColor: '#F43F5E',
      borderVisible: false,
      wickUpColor: '#10B981',
      wickDownColor: '#F43F5E',
    });
    candleSeries.setData(candles.map(({ time, open, high, low, close }) => ({ time, open, high, low, close })));

    // volume histogram overlaid at the bottom of the price pane
    const volSeries = chart.addSeries(HistogramSeries, {
      priceScaleId: 'vol',
      priceFormat: { type: 'volume' },
      lastValueVisible: false,
      priceLineVisible: false,
    });
    volSeries
      .priceScale()
      .applyOptions({ scaleMargins: { top: 0.85, bottom: 0 }, visible: false });
    volSeries.setData(
      candles.map((c) => ({
        time: c.time,
        value: c.volume,
        color: c.close >= c.open ? 'rgba(16, 185, 129, 0.35)' : 'rgba(244, 63, 94, 0.35)',
      })),
    );

    const lineOpts = { lineWidth: 1.6, lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false };
    if (overlays) {
      if (enabled.ema20) chart.addSeries(LineSeries, { ...lineOpts, color: '#38BDF8' }).setData(overlays.ema20);
      if (enabled.ema50) chart.addSeries(LineSeries, { ...lineOpts, color: '#A78BFA' }).setData(overlays.ema50);
      if (enabled.ema200) chart.addSeries(LineSeries, { ...lineOpts, color: '#F59E0B' }).setData(overlays.ema200);
      if (enabled.bb) {
        chart.addSeries(LineSeries, { ...lineOpts, color: 'rgba(100,116,139,0.8)', lineStyle: 2 }).setData(overlays.bbUpper);
        chart.addSeries(LineSeries, { ...lineOpts, color: 'rgba(100,116,139,0.8)', lineStyle: 2 }).setData(overlays.bbLower);
      }
      if (enabled.supertrend) {
        chart.addSeries(LineSeries, { ...lineOpts, color: '#10B981', lineWidth: 2 }).setData(overlays.supertrend);
      }

      // RSI pane
      const rsiSeries = chart.addSeries(LineSeries, { ...lineOpts, color: '#38BDF8', lastValueVisible: true }, 1);
      rsiSeries.setData(overlays.rsi);
      rsiSeries.createPriceLine({ price: 70, color: 'rgba(244,63,94,0.5)', lineStyle: 2, lineWidth: 1, axisLabelVisible: false });
      rsiSeries.createPriceLine({ price: 30, color: 'rgba(16,185,129,0.5)', lineStyle: 2, lineWidth: 1, axisLabelVisible: false });

      // MACD pane
      const macdHist = chart.addSeries(HistogramSeries, { lastValueVisible: false, priceLineVisible: false }, 2);
      macdHist.setData(
        overlays.macdHist.map((p) => ({
          ...p,
          color: p.value >= 0 ? 'rgba(16,185,129,0.55)' : 'rgba(244,63,94,0.55)',
        })),
      );
      chart.addSeries(LineSeries, { ...lineOpts, color: '#38BDF8' }, 2).setData(overlays.macd);
      chart.addSeries(LineSeries, { ...lineOpts, color: '#F59E0B' }, 2).setData(overlays.macdSignal);

      const panes = chart.panes();
      if (panes[1]) panes[1].setHeight(95);
      if (panes[2]) panes[2].setHeight(95);
    }

    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [candles, overlays, enabled]);

  return (
    <div>
      {overlays && (
        <div className="mb-3 flex flex-wrap items-center gap-1.5">
          {OVERLAY_DEFS.map((o) => (
            <button
              key={o.key}
              onClick={() => setEnabled((e) => ({ ...e, [o.key]: !e[o.key] }))}
              className={`chip transition-colors ${
                enabled[o.key] ? 'bg-ink-600 text-white ring-1 ring-ink-500' : 'bg-ink-800 text-slate-500 hover:text-slate-300'
              }`}
            >
              <span className="h-1.5 w-1.5 rounded-full" style={{ background: o.color }} />
              {o.label}
            </button>
          ))}
          <span className="ml-auto hidden text-[11px] text-slate-500 sm:block">RSI & MACD panes below · scroll to zoom</span>
        </div>
      )}
      <div ref={containerRef} style={{ height }} />
    </div>
  );
}
