# TrendWise — Indian Stock & ETF Analysis Engine

An intelligent technical-analysis engine for **Indian equities and ETFs (NSE)** with a modern, brand-quality web UI. It computes 15+ technical indicators, scores them into a single **Strong Buy → Strong Sell verdict**, generates a concrete **trade plan** (entry zone, stop-loss, targets, risk-reward), and layers in **news sentiment** from free RSS feeds.

> ⚠️ **Disclaimer**: TrendWise is an educational analysis tool, **not SEBI-registered investment advice**. Technical signals are probabilistic, not guarantees. Always do your own research before trading.

## Features

- **Indicator engine** (pure pandas, unit-tested): SMA/EMA 20·50·100·200, RSI, MACD, Stochastic, ROC, CCI, ATR, Bollinger Bands, ADX/DI, Supertrend, Ichimoku Cloud, OBV, Chaikin Money Flow, rolling VWAP
- **Weighted confluence scoring**: each indicator votes −2…+2 with a weight; the normalized −100…+100 score maps to a verdict, with a plain-English reason for every vote
- **Higher-timeframe filter**: weekly trend softens counter-trend daily signals
- **Trade plans**: entry zone / pullback logic, ATR + swing-low stop-loss, 1.5R / 2.5R targets, risk-reward, resistance warnings
- **News sentiment**: Economic Times / Moneycontrol / LiveMint RSS + Google News per stock, scored with VADER + a finance lexicon; nudges the composite score by up to ±10
- **Market overview**: NIFTY/SENSEX/BANKNIFTY, top gainers/losers, advance-decline breadth
- **Screener**: 10 scans (Strong Buy, oversold RSI, golden cross, near 52-week high, high volume, strong trend, …) across 125 NSE equities and 20 ETFs
- **ETF suggestions**: top 3 ETFs per category (index, gold, sector, factor, international, debt) ranked by composite signal score
- **Mutual funds** (mfapi.in / AMFI NAV data): fund search, trailing returns (1M–5Y), volatility, max drawdown, monthly-SIP illustration, and top funds per category (Flexi/Large/Mid/Small Cap, ELSS, Index, Liquid) ranked by 3Y CAGR — NAV-based logic, not candle indicators, since NAV updates once a day
- **My First Portfolio** (`/start`): a guided finder for new investors — a 3-question quiz (horizon, reaction to a fall, emergency fund) maps to Conservative / Balanced / Growth, then builds a starter mix of ETFs + mutual funds with an allocation percentage per pick, a job line (core / engine / cushion), numbered pros/cons, and a monthly-SIP rupee split. ETF index slot: broad-index names first, then highest score; gold slot fixed by role; liquid slot picked for stability with its trend verdict suppressed. Mutual-fund slots: best risk-adjusted return (3Y CAGR / volatility) among each category's top leaders, Direct Growth plans only. No small-cap in any beginner portfolio; expense ratio, manager tenure and holdings overlap are not available from the data sources and are flagged as such
- **Watchlist + signal history**: SQLite by default, Supabase (free Postgres) when configured
- **Live data only**: prices come from Yahoo Finance's public chart API — there is no synthetic fallback; when the feed fails, endpoints return an honest error instead of made-up numbers

## Stack (all free)

| Layer | Tech |
|---|---|
| Backend | Python 3.11, FastAPI, pandas, requests, feedparser, vaderSentiment, APScheduler |
| Frontend | React 18, Vite, Tailwind CSS, TradingView lightweight-charts v5 |
| Database | SQLite (default) or Supabase free tier |
| Data | Yahoo Finance (NSE `.NS` tickers), free RSS news feeds, mfapi.in (AMFI NAV data) — no API keys |

## Quickstart

**Backend** (http://localhost:8000, docs at `/docs`):

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend** (http://localhost:5173, proxies `/api` to the backend):

```bash
cd frontend
npm install
npm run dev
```

Run backend tests: `cd backend && python -m pytest tests/`

## Configuration (env vars, all optional)

| Variable | Default | Purpose |
|---|---|---|
| `SUPABASE_URL` / `SUPABASE_KEY` | — | Use Supabase instead of SQLite (run `backend/supabase_schema.sql` first) |
| `SQLITE_PATH` | `backend/trendwise.db` | Local database location |
| `SCHEDULER` | `on` | Background cache pre-warming (market 5m, screener 15m, news 10m) |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `QUOTE_TTL` / `HISTORY_TTL` / `NEWS_TTL` / `ANALYSIS_TTL` | 120/3600/900/600 s | Cache tuning |
| `VITE_API_URL` (frontend) | — | Backend URL in production builds |

## API overview

| Endpoint | Purpose |
|---|---|
| `GET /api/symbols/search?q=` | Symbol autocomplete |
| `GET /api/stocks/{symbol}/quote` | Quote + day stats |
| `GET /api/stocks/{symbol}/history?range=1y` | OHLCV + indicator overlay series |
| `GET /api/stocks/{symbol}/analysis` | Full report: votes, score, verdict, levels, trade plan |
| `GET /api/stocks/{symbol}/news` | Headlines with per-article sentiment |
| `GET /api/stocks/{symbol}/signal-history` | Daily verdict snapshots |
| `GET /api/market/overview` | Indices, movers, breadth |
| `GET /api/screener?scan=strong_buy&type=equity` | Signal scans (`/api/screener/scans` lists all) |
| `GET /api/etfs` | Curated ETF list |
| `GET/POST/DELETE /api/watchlist?client_id=` | Watchlist CRUD |

## Free deployment

1. **Backend → Render/Railway free tier**: root `backend/`, start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. The app serves live data only — no demo mode exists.
2. **Database → Supabase**: create a free project, run `backend/supabase_schema.sql` in the SQL editor, set `SUPABASE_URL` + `SUPABASE_KEY` on the backend.
3. **Frontend → Vercel/Netlify**: root `frontend/`, build `npm run build`, output `dist/`, env `VITE_API_URL=https://<your-backend>`.

## Notes & limits

- Yahoo Finance is the pragmatic free source for NSE data (official NSE APIs block automated clients). Everything is cached (quotes ~2 min, EOD history 1 h) to stay well inside informal limits.
- The screener's first cold run analyzes the whole universe (~1–2 min live); the scheduler keeps it warm afterwards.
- Signals describe *technical posture*, not certainty. The weighted-confluence approach rewards agreement between independent indicator families (trend, momentum, volume, volatility) — the same logic a discretionary trader applies by eye, made systematic and explainable.
