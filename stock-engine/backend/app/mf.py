"""Mutual fund data + analysis on top of the free mfapi.in service (AMFI data).

Why MFs get different logic from stocks/ETFs:
- Funds are NOT exchange-traded: there are no intraday candles, so the
  15-indicator engine (RSI/MACD/etc.) is meaningless on NAV. MF logic is
  NAV-based instead: trailing returns, volatility, max drawdown, and a
  monthly-SIP illustration.
- mfapi.in is a free community mirror of AMFI data, not an official feed.
  Every call can fail; callers must degrade gracefully (503), never crash.
- Rankings are past-performance shortlists, NOT recommendations. Every
  response carries its method and the past-performance disclaimer.
"""
import json
import logging
import math
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta

from .data.cache import cached

log = logging.getLogger(__name__)

MFAPI = "https://api.mfapi.in"
LIST_TTL = 86400
DETAIL_TTL = 86400
STALE_DAYS = 10

CATEGORIES = {
    "flexi-cap": ["Flexi Cap"],
    "large-cap": ["Large Cap"],
    "mid-cap": ["Mid Cap"],
    "small-cap": ["Small Cap"],
    "elss": ["ELSS", "Tax Saver"],
    "index": ["Index"],
    "liquid": ["Liquid"],
}

HORIZONS = [  # label, lookback observations (business days, approx)
    ("1M", 22),
    ("3M", 66),
    ("6M", 132),
    ("1Y", 252),
    ("3Y", 756),
    ("5Y", 1260),
]

DISCLAIMER = (
    "Past performance does not guarantee future returns. Rankings use "
    "historical NAV only and are educational, not investment advice."
)


def _get_json(url: str, timeout: int = 20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TrendWise/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        log.warning("mfapi fetch failed for %s: %s", url, exc)
        return None


def scheme_list() -> list | None:
    return cached("mf:list", LIST_TTL, lambda: _get_json(f"{MFAPI}/mf"))


def search_schemes(query: str, limit: int = 15) -> list:
    lst = scheme_list()
    if not lst:
        return []
    q = query.strip().lower()
    starts, contains = [], []
    for s in lst:
        name = (s.get("schemeName") or "")
        if not name:
            continue
        item = {"schemeCode": s["schemeCode"], "schemeName": name}
        if name.lower().startswith(q):
            starts.append(item)
        elif q in name.lower():
            contains.append(item)
    return (starts + contains)[:limit]


def base_name(name: str) -> str:
    """Strip plan/option suffixes so Direct + Regular variants dedupe."""
    out = re.sub(r"\s*-\s*(Direct|Regular) Plan\s*-\s*.*$", "", name, flags=re.I)
    out = re.sub(r"\s*-\s*(Growth|IDCW.*|Dividend.*)$", "", out, flags=re.I)
    return out.strip()


def _is_growth_plan(name: str) -> bool:
    low = name.lower()
    return "growth" in low and "idcw" not in low and "dividend" not in low


def matches_category(name: str, category: str) -> bool:
    keywords = CATEGORIES.get(category) or []
    low = name.lower()
    return any(k.lower() in low for k in keywords)


def scheme_detail(code: int | str) -> dict | None:
    return cached(f"mf:detail:{code}", DETAIL_TTL, lambda: _fetch_detail(code))


def _fetch_detail(code: int | str) -> dict | None:
    raw = _get_json(f"{MFAPI}/mf/{code}")
    if not raw or not raw.get("data"):
        return None
    nav = []
    for row in raw["data"]:
        try:
            d = datetime.strptime(row["date"], "%d-%m-%Y").date()
            v = float(row["nav"])
        except (KeyError, ValueError, TypeError):
            continue
        if v > 0:
            nav.append((d, v))
    if len(nav) < 30:
        return None
    nav.sort()
    return {"meta": raw.get("meta") or {}, "nav": nav}


def _returns(nav: list) -> dict:
    """Trailing returns per horizon: absolute %, plus CAGR for >= 1Y."""
    out = {}
    n = len(nav)
    last_date, last_nav = nav[-1]
    for label, lookback in HORIZONS:
        if n <= lookback:
            continue
        start_date, start_nav = nav[-1 - lookback]
        days = (last_date - start_date).days or 1
        ret = last_nav / start_nav - 1
        # Annualize only for ~1Y+ windows (252 trading days ≈ 352 calendar days);
        # short-horizon returns are reported absolute, never annualized.
        cagr = (last_nav / start_nav) ** (365.0 / days) - 1 if days >= 300 else None
        out[label] = {
            "returnPct": round(ret * 100, 2),
            "cagrPct": round(cagr * 100, 2) if cagr is not None else None,
        }
    return out


def _volatility(nav: list) -> float | None:
    """Annualized std-dev of daily log returns over the last ~1Y."""
    window = nav[-253:] if len(nav) > 253 else nav
    if len(window) < 30:
        return None
    rets = [math.log(window[i][1] / window[i - 1][1]) for i in range(1, len(window))]
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / len(rets)
    return round(math.sqrt(var) * math.sqrt(252) * 100, 2)


def _max_drawdown(nav: list) -> float | None:
    window = nav[-757:] if len(nav) > 757 else nav
    if len(window) < 30:
        return None
    peak = window[0][1]
    worst = 0.0
    for _, v in window:
        peak = max(peak, v)
        worst = min(worst, v / peak - 1)
    return round(worst * 100, 2)


def _sip(nav: list, monthly: float = 10000) -> dict:
    """Monthly-SIP illustration: invest at each month-end NAV, value at latest NAV."""
    month_end: dict[tuple[int, int], float] = {}
    for d, v in nav:
        month_end[(d.year, d.month)] = v  # last observation of each month wins
    months = sorted(month_end)
    out = {}
    last_nav = nav[-1][1]
    for label, count in (("1Y", 12), ("3Y", 36), ("5Y", 60)):
        if len(months) < count:
            continue
        points = [month_end[m] for m in months[-count:]]
        units = sum(monthly / p for p in points)
        value = units * last_nav
        invested = monthly * count
        gain = value / invested - 1
        out[label] = {
            "invested": round(invested, 2),
            "value": round(value, 2),
            "gainPct": round(gain * 100, 2),
            "annualizedPct": round(((value / invested) ** (12.0 / count) - 1) * 100, 2),
        }
    return out


def fund_report(code: int | str) -> dict | None:
    detail = scheme_detail(code)
    if not detail:
        return None
    meta, nav = detail["meta"], detail["nav"]
    last_date, last_nav = nav[-1]
    return {
        "schemeCode": meta.get("scheme_code", code),
        "schemeName": meta.get("scheme_name"),
        "fundHouse": meta.get("fund_house"),
        "category": meta.get("scheme_category"),
        "type": meta.get("scheme_type"),
        "latestNav": round(last_nav, 4),
        "navDate": last_date.isoformat(),
        "returns": _returns(nav),
        "volatilityPct": _volatility(nav),
        "maxDrawdownPct": _max_drawdown(nav),
        "sip": _sip(nav),
        "historyPoints": len(nav),
        "disclaimer": DISCLAIMER,
    }


def _leader_row(code: int, name: str) -> dict | None:
    report = fund_report(code)
    if not report:
        return None
    # Skip stale funds (dead/merged schemes linger in the mfapi list).
    try:
        nav_date = date.fromisoformat(report["navDate"])
    except ValueError:
        return None
    if (date.today() - nav_date).days > STALE_DAYS:
        return None
    rets = report["returns"]
    rank_key = (rets.get("3Y") or {}).get("cagrPct")
    if rank_key is None:
        rank_key = (rets.get("1Y") or {}).get("returnPct")
    if rank_key is None:
        return None
    return {
        "schemeCode": report["schemeCode"],
        "schemeName": report["schemeName"],
        "fundHouse": report["fundHouse"],
        "category": report["category"],
        "return1Y": (rets.get("1Y") or {}).get("returnPct"),
        "cagr3Y": (rets.get("3Y") or {}).get("cagrPct"),
        "volatilityPct": report["volatilityPct"],
        "rankValue": rank_key,
    }


def category_leaders(category: str, limit: int = 5, candidates: int = 40) -> dict | None:
    return cached(
        f"mf:leaders:{category}:{limit}:{candidates}", DETAIL_TTL,
        lambda: _category_leaders(category, limit, candidates),
    )


def _category_leaders(category: str, limit: int, candidates: int = 40) -> dict | None:
    keywords = CATEGORIES.get(category)
    if not keywords:
        return None
    lst = scheme_list()
    if not lst:
        return None
    # Growth plans only; dedupe Direct/Regular by base fund name, prefer Direct.
    by_base: dict[str, dict] = {}
    for s in lst:
        name = s.get("schemeName") or ""
        if not _is_growth_plan(name):
            continue
        if not matches_category(name, category):
            continue
        base = base_name(name)
        prev = by_base.get(base)
        if prev is None or ("direct" in name.lower() and "direct" not in prev["name"].lower()):
            by_base[base] = {"code": s["schemeCode"], "name": name}
    candidates = list(by_base.values())[:candidates]
    if not candidates:
        return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = [r for r in pool.map(lambda c: _leader_row(c["code"], c["name"]), candidates) if r]
    rows.sort(key=lambda r: r["rankValue"], reverse=True)
    leaders = rows[:limit]
    for r in leaders:
        r.pop("rankValue", None)
    return {
        "category": category,
        "leaders": leaders,
        "candidates": len(candidates),
        "method": (
            f"Growth plans matching '{category}' by scheme name "
            f"({len(candidates)} with fresh NAVs), ranked by 3Y CAGR "
            "(1Y return where 3Y is unavailable). " + DISCLAIMER
        ),
    }
