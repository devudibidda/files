# TrendWise — Indian Stock Market Analysis Engine (Plan)

An intelligent analysis engine for **Indian equities & ETFs (NSE/BSE)** that computes a full suite of technical indicators, generates **entry / buy / sell signals** with stop-loss and targets, layers in **news sentiment**, and presents everything in a **modern, brand-quality web UI**.

> ⚠️ Product-wide disclaimer: educational analysis tool, **not SEBI-registered investment advice**. This disclaimer will be shown in the UI.

---

## 1. Tech Stack (100% free tier)

| Layer | Choice | Why |
|---|---|---|
| Backend | **Python 3.11 + FastAPI** | Async, fast, auto OpenAPI docs |
| Indicators | **pandas + `pandas-ta`** | Pure-python TA library, no TA-Lib C build headaches |
| Market data | **yfinance** (Yahoo Finance) | Free, reliable for NSE (`.NS`) / BSE (`.BO`) tickers, OHLCV daily + intraday |
| Backup data | NSE India public endpoints (indices, top gainers/losers) | Free, used with caching + graceful fallback |
| News | **RSS feeds** (Economic Times Markets, Moneycontrol, LiveMint, Business Standard) + **Google News RSS** per-stock query | Free, no API key, no rate-limit pain |
| Sentiment | **VADER** (nltk) with a finance keyword boost list | Free, fast, no GPU |
| Database | **Supabase** (free Postgres) | Watchlists, cached analyses, signal history; local SQLite fallback for dev |
| Scheduler | **APScheduler** in the backend | Refresh EOD data + news periodically |
| Frontend | **React 18 + Vite + Tailwind CSS** | Modern, fast dev loop |
| Charts | **TradingView `lightweight-charts`** (candles) + **Recharts** (indicator panels, gauges) | Free, professional look |
| Deploy (later) | Render/Railway (API) + Vercel (UI) + Supabase (DB) | All free tiers |

---

## 2. Architecture

```
┌─────────────────────────────┐
│  React + Tailwind (Vercel)  │  Dashboard, Stock page, Screener, Watchlist
└──────────────┬──────────────┘
               │ REST (JSON)
┌──────────────▼──────────────┐
│        FastAPI backend      │
│  ┌───────────────────────┐  │
│  │ Data Layer            │  │ yfinance fetcher + cache, NSE symbols master
│  ├───────────────────────┤  │
│  │ Indicator Engine      │  │ 15+ indicators via pandas-ta
│  ├───────────────────────┤  │
│  │ Signal Engine         │  │ Weighted confluence score → verdict + entry/SL/targets
│  ├───────────────────────┤  │
│  │ News + Sentiment      │  │ RSS aggregation + VADER scoring
│  ├───────────────────────┤  │
│  │ Scheduler             │  │ EOD refresh, news refresh, signal snapshots
│  └───────────────────────┘  │
└──────────────┬──────────────┘
               │
      Supabase Postgres  (watchlists, analysis cache, signal history)
```

---

## 3. Analysis Engine (the core intelligence)

### 3.1 Indicators computed per symbol (daily + weekly timeframes)
- **Trend**: SMA/EMA 20·50·100·200, Supertrend (10,3), ADX/DI, Ichimoku Cloud, MACD (12,26,9)
- **Momentum**: RSI (14), Stochastic (14,3,3), ROC, CCI
- **Volatility**: Bollinger Bands (20,2), ATR (14)
- **Volume**: OBV, 20-day volume ratio, VWAP (intraday), Chaikin Money Flow
- **Levels**: classic pivot points, swing-based support/resistance zones, 52-week high/low distance

### 3.2 Signal Engine — weighted confluence scoring
Each indicator votes **−2 … +2** with a weight (trend indicators weigh more than oscillators). The normalized composite score (−100 … +100) maps to a verdict:

| Score | Verdict |
|---|---|
| ≥ 60 | **Strong Buy** |
| 20 … 60 | Buy |
| −20 … 20 | Hold / Neutral |
| −60 … −20 | Sell |
| ≤ −60 | **Strong Sell** |

News sentiment adjusts the score by up to ±10 and is reported separately.

### 3.3 Trade plan (for Buy verdicts)
- **Entry zone**: current price vs. nearest support / EMA20 pullback logic
- **Stop-loss**: `entry − 2×ATR` (or below the nearest swing-low, whichever is tighter)
- **Targets**: T1 = 1.5R, T2 = 2.5R (R = entry − stop-loss); capped at nearest resistance
- **Risk-reward ratio** shown explicitly; setups with RR < 1.5 flagged

### 3.4 Detailed analysis report (per stock)
For every indicator: current value, state (bullish/bearish/neutral), and a **plain-English explanation** ("RSI at 62 shows healthy momentum without being overbought"). Plus trend summary, key levels table, sentiment digest of latest headlines, and signal history.

---

## 4. API Design (FastAPI)

| Endpoint | Purpose |
|---|---|
| `GET /api/symbols/search?q=` | Symbol autocomplete (equities + ETFs master list) |
| `GET /api/stocks/{symbol}/quote` | Live quote, day stats |
| `GET /api/stocks/{symbol}/history?range=&interval=` | OHLCV for charts |
| `GET /api/stocks/{symbol}/analysis` | **Full report**: indicators, score, verdict, trade plan |
| `GET /api/stocks/{symbol}/news` | Headlines + sentiment per article |
| `GET /api/market/overview` | NIFTY 50 / SENSEX / BANKNIFTY, gainers/losers, breadth |
| `GET /api/screener?filter=` | Pre-built scans: Strong Buy today, RSI oversold, Golden Cross, 52-w breakout, high-volume movers |
| `GET/POST/DELETE /api/watchlist` | Watchlist CRUD (Supabase) |
| `GET /api/etfs` | Curated NSE ETF list (Nifty BeES, Gold BeES, etc.) with analysis |

---

## 5. Frontend (modern, brand-quality UI)

**Design language**: dark-first fintech aesthetic (deep navy/near-black surfaces, emerald=bullish / rose=bearish accents), Inter font, glassy cards, subtle micro-interactions, fully responsive, light-mode toggle.

Pages:
1. **Dashboard** — index tickers strip, market breadth, top gainers/losers, "Today's Strong Buys", news feed with sentiment chips
2. **Stock Analysis page** (the hero) —
   - Candlestick chart with toggleable overlays (EMAs, Bollinger, Supertrend) + RSI/MACD/volume sub-panels
   - **Verdict card**: score gauge, Strong Buy→Strong Sell dial, confidence
   - **Trade plan card**: entry zone, stop-loss, T1/T2, risk-reward
   - Indicator breakdown table with plain-English reasons
   - Support/resistance levels, news + sentiment tab
3. **Screener** — filterable signal scans across NIFTY 500 + ETFs
4. **ETF hub** — curated ETF list with the same analysis
5. **Watchlist** — saved symbols with live verdict chips

---

## 6. Repo layout

```
stock-engine/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app + routers
│   │   ├── data/              # yfinance fetcher, symbol master, cache
│   │   ├── indicators/        # indicator engine
│   │   ├── signals/           # scoring, verdicts, trade plans
│   │   ├── news/              # RSS + sentiment
│   │   ├── db/                # Supabase/SQLite layer
│   │   └── scheduler.py
│   ├── tests/
│   └── requirements.txt
└── frontend/
    ├── src/ (components, pages, hooks, api client)
    ├── tailwind.config.js
    └── package.json
```

---

## 7. Implementation phases

1. **Phase 1 — Backend core**: project scaffold, symbol master (NIFTY 500 + ETFs), yfinance data layer with caching, indicator engine + tests
2. **Phase 2 — Intelligence**: signal engine (scoring, verdicts, trade plans), support/resistance detection, analysis report endpoint
3. **Phase 3 — News & market**: RSS aggregation + VADER sentiment, market overview, screener scans, scheduler
4. **Phase 4 — Frontend**: React/Tailwind scaffold + design system, dashboard, stock analysis page with charts, screener, ETF hub, watchlist
5. **Phase 5 — Persistence & polish**: Supabase integration (watchlist, signal history), loading/error states, disclaimer, README, deployment guides

Each phase ends with a commit; the app is runnable locally after Phase 4 (`uvicorn` + `vite dev`).

---

## 8. Known constraints & mitigations
- **yfinance rate limits / hiccups** → in-memory + DB caching (quotes 1–5 min, EOD history 24 h), retry with backoff
- **NSE official APIs block bots** → treated as optional enrichment only; yfinance is the source of truth
- **Free news APIs have tiny quotas** → RSS-first strategy needs no keys at all
- **Supabase optional in dev** → SQLite fallback so anyone can run it with zero setup
