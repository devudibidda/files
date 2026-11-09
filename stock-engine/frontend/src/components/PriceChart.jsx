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
    textColor: '#87867f',
    fontFamily: 'Inter, system-ui, sans-serif',
    panes: { separatorColor: '#e3dacc', separatorHoverColor: '#cccbc8' },
  },
  grid: {
    vertLines: { color: 'rgba(227, 218, 204, 0.6)' },
    horzLines: { color: 'rgba(227, 218, 204, 0.6)' },
  },
  crosshair: {
    vertLine: { color: '#87867f', labelBackgroundColor: '#121212' },
    horzLine: { color: '#87867f', labelBackgroundColor: '#121212' },
  },
  rightPriceScale: { borderColor: '#e3dacc' },
  timeScale: { borderColor: '#e3dacc', rightOffset: 4 },
  autoSize: true,
};

const OVERLAY_DEFS = [
  { key: 'ema20', label: 'EMA 20', color: '#d97757' },
  { key: 'ema50', label: 'EMA 50', color: '#3d3d3a' },
  { key: 'ema200', label: 'EMA 200', color: '#b0aea5' },
  { key: 'bb', label: 'Bollinger', color: '#87867f' },
  { key: 'supertrend', label: 'Supertrend', color: '#02a745' },
];

export default function PriceChart({ candles, overlays, height = 560 }) {
  const containerRef = useRef(null);
  const [enabled, setEnabled] = useState({ ema20: true, ema50: true, ema200: true, bb: false, supertrend: false });

  useEffect(() => {
    if (!containerRef.current || !candles?.length) return;

    const chart = createChart(containerRef.current, CHART_OPTS);

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#02a745',
      downColor: '#a10214',
      borderVisible: false,
      wickUpColor: '#02a745',
      wickDownColor: '#a10214',
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
        color: c.close >= c.open ? 'rgba(2, 167, 69, 0.35)' : 'rgba(161, 2, 20, 0.35)',
      })),
    );

    const lineOpts = { lineWidth: 1.6, lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false };
    if (overlays) {
      if (enabled.ema20) chart.addSeries(LineSeries, { ...lineOpts, color: '#d97757' }).setData(overlays.ema20);
      if (enabled.ema50) chart.addSeries(LineSeries, { ...lineOpts, color: '#3d3d3a' }).setData(overlays.ema50);
      if (enabled.ema200) chart.addSeries(LineSeries, { ...lineOpts, color: '#b0aea5' }).setData(overlays.ema200);
      if (enabled.bb) {
        chart.addSeries(LineSeries, { ...lineOpts, color: 'rgba(135,134,127,0.8)', lineStyle: 2 }).setData(overlays.bbUpper);
        chart.addSeries(LineSeries, { ...lineOpts, color: 'rgba(135,134,127,0.8)', lineStyle: 2 }).setData(overlays.bbLower);
      }
      if (enabled.supertrend) {
        chart.addSeries(LineSeries, { ...lineOpts, color: '#02a745', lineWidth: 2 }).setData(overlays.supertrend);
      }

      // RSI pane
      const rsiSeries = chart.addSeries(LineSeries, { ...lineOpts, color: '#d97757', lastValueVisible: true }, 1);
      rsiSeries.setData(overlays.rsi);
      rsiSeries.createPriceLine({ price: 70, color: 'rgba(161,2,20,0.5)', lineStyle: 2, lineWidth: 1, axisLabelVisible: false });
      rsiSeries.createPriceLine({ price: 30, color: 'rgba(2,167,69,0.5)', lineStyle: 2, lineWidth: 1, axisLabelVisible: false });

      // MACD pane
      const macdHist = chart.addSeries(HistogramSeries, { lastValueVisible: false, priceLineVisible: false }, 2);
      macdHist.setData(
        overlays.macdHist.map((p) => ({
          ...p,
          color: p.value >= 0 ? 'rgba(2,167,69,0.55)' : 'rgba(161,2,20,0.55)',
        })),
      );
      chart.addSeries(LineSeries, { ...lineOpts, color: '#3d3d3a' }, 2).setData(overlays.macd);
      chart.addSeries(LineSeries, { ...lineOpts, color: '#c6613f' }, 2).setData(overlays.macdSignal);

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
                enabled[o.key] ? 'bg-slate-100 text-white ring-1 ring-slate-100' : 'bg-ink-800 text-slate-500 hover:text-slate-300'
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
