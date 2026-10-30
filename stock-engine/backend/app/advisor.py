"""My First Portfolio: guided starter portfolios for new investors.

Strategy, synthesized 30 Oct 2026 from a three-agent brainstorm
(educator + quant + skeptic):
- A 3-question quiz maps to Conservative / Balanced / Growth.
- At most 4 picks per portfolio; no small-cap anywhere for beginners.
- ETF index slot: broad-index names first (Nifty 50 / Next 50), then the
  highest trend score. Gold slot is fixed by role (GOLDBEES). Liquid
  slot is picked for stability only — its trend verdict is suppressed,
  because liquid-ETF prices barely move and the score is noise.
- Mutual-fund slot: best risk-adjusted return (3Y CAGR / volatility)
  among the top leaders of its category, Direct Growth plans only.
  A negative 1Y return is flagged as a con, never hidden.
- Every pick carries numbered pros/cons, a job line ("core / engine /
  cushion") and an allocation percentage; allocations sum to 100.
- Nothing here is a recommendation: past performance does not
  guarantee future returns, and several inputs a real adviser would
  want (expense ratio, fund-manager tenure, holdings overlap, exit
  loads) are not available from the data sources used.
"""

from concurrent.futures import ThreadPoolExecutor

from . import mf
from .data.cache import cached
from .screener import scan_universe

FINDER_TTL = 86400  # portfolio picks re-ranked at most daily

DISCLAIMER = (
    "Past performance does not guarantee future returns — this is an "
    "educational shortlist, not personal investment advice, so check "
    "each fund's risk, costs, and fit for your time horizon before "
    "investing."
)

KEY_SENTENCE = (
    "Start with a small monthly SIP, review only once a year, and let "
    "time — not timing — do the work."
)

PROFILES = {
    "conservative": {
        "label": "Conservative",
        "line": "Money you may need soon, or a low tolerance for falls. "
                 "Stability leads; equities ride only in the core.",
        "slots": [("index_etf", 40), ("large_cap_mf", 25),
                  ("liquid", 25), ("gold_etf", 10)],
    },
    "balanced": {
        "label": "Balanced",
        "line": "A few years of horizon and a steady stomach. "
                 "A growth engine plus a hedge.",
        "slots": [("index_etf", 30), ("flexi_cap_mf", 35),
                  ("large_cap_mf", 20), ("gold_etf", 15)],
    },
    "growth": {
        "label": "Growth",
        "line": "Five-plus years ahead, and you keep investing through falls. "
                 "The engine runs hotter, with mid-caps in the mix.",
        "slots": [("index_etf", 35), ("flexi_cap_mf", 35),
                  ("mid_cap_mf", 20), ("gold_etf", 10)],
    },
}

JOBS = {
    "index_etf": "Core — steady market return",
    "large_cap_mf": "Engine — higher growth, bigger swings",
    "flexi_cap_mf": "Engine — higher growth, bigger swings",
    "mid_cap_mf": "Engine — higher growth, bigger swings",
    "liquid": "Cushion — steadies the ride",
    "gold_etf": "Cushion — steadies the ride",
}

MF_CATEGORY = {
    "large_cap_mf": "large-cap",
    "flexi_cap_mf": "flexi-cap",
    "mid_cap_mf": "mid-cap",
}

# Broad market indices only — sector, bank, mid-cap and small-cap ETFs
# must never win the "index" slot on score alone.
BROAD_INDEX_MARKERS = ("Nifty 50", "Next 50")


def _inr(value: float) -> str:
    """Indian digit grouping: 412749 -> '4,12,749'."""
    s = f"{abs(value):.0f}"
    if len(s) <= 3:
        out = s
    else:
        out, rest = s[-3:], s[:-3]
        while rest:
            out, rest = rest[-2:] + "," + out, rest[:-2]
    return ("-" if value < 0 else "") + out


def profile_for(horizon: str, reaction: str) -> str:
    """Quiz answers -> profile. Horizon dominates: money needed soon
    must not ride stock-market swings, whatever the risk appetite."""
    if horizon == "short" or reaction == "panic":
        return "conservative"
    if horizon == "long" and reaction == "invest":
        return "growth"
    return "balanced"


def pick_etf(role: str, rows: list[dict] | None = None) -> dict | None:
    rows = rows if rows is not None else scan_universe("etf")
    if role == "index_etf":
        broad = [r for r in rows
                 if r.get("sector") == "Index ETF"
                 and any(m in (r.get("name") or "") for m in BROAD_INDEX_MARKERS)]
        pool = broad or [r for r in rows if r.get("sector") == "Index ETF"]
        if not pool:
            return None
        row = max(pool, key=lambda r: r.get("score") or 0)
        note = ("Highest trend score among broad-index ETFs."
                if broad else "Highest trend score among index ETFs.")
    elif role == "gold_etf":
        row = next((r for r in rows if r.get("symbol") == "GOLDBEES"), None)
        if row is None:
            row = next((r for r in rows if r.get("sector") == "Gold ETF"), None)
        if row is None:
            return None
        note = ("The only gold ETF in the universe — this slot is fixed "
                "by role, not by score.")
    elif role == "liquid":
        row = next((r for r in rows if r.get("symbol") == "LIQUIDBEES"), None)
        if row is None:
            row = next((r for r in rows if r.get("sector") == "Debt ETF"), None)
        if row is None:
            return None
        note = ("Picked for stability, not score — liquid-ETF prices "
                "barely move, so trend scores are meaningless here.")
    else:
        return None
    return {
        "kind": "etf",
        "symbol": row.get("symbol"),
        "name": row.get("name"),
        "source": row.get("source"),
        "score": row.get("score"),
        "verdict": None if role == "liquid" else row.get("verdict"),
        "ratingNote": ("Not rated — price barely moves, so trend scores "
                       "don't apply here.") if role == "liquid" else None,
        "selectionNote": note,
    }


def pick_mf(category: str) -> dict | None:
    """Best risk-adjusted leader of a mutual-fund category.

    Ranks the category's top 5 leaders by 3Y CAGR / volatility (falls
    back to 3Y CAGR alone when volatility is missing), Direct Growth
    plans only, then enriches the winner with its full report so the
    pros/cons can quote drawdown and SIP numbers.
    """
    leaders = mf.category_leaders(category, limit=5, candidates=20)
    if not leaders or not leaders.get("leaders"):
        return None
    rows = leaders["leaders"]
    pool = [r for r in rows if r.get("cagr3Y") is not None] or rows

    def risk_adjusted(r: dict) -> float:
        cagr = r.get("cagr3Y")
        vol = r.get("volatilityPct")
        if cagr is None:
            return float("-inf")
        return cagr / vol if vol else cagr

    best = max(pool, key=risk_adjusted)
    report = mf.fund_report(best["schemeCode"]) or {}
    return {
        "kind": "mf",
        "schemeCode": best["schemeCode"],
        "name": best["schemeName"],
        "fundHouse": best.get("fundHouse"),
        "category": category,
        "return1Y": best.get("return1Y"),
        "cagr3Y": best.get("cagr3Y"),
        "volatilityPct": best.get("volatilityPct"),
        "maxDrawdownPct": report.get("maxDrawdownPct"),
        "sip3Y": (report.get("sip") or {}).get("3Y"),
        "navDate": report.get("navDate"),
        "selectionNote": (
            f"Best risk-adjusted return (3Y CAGR / volatility) among the "
            f"top {len(rows)} {category} Growth plans scanned "
            f"({leaders.get('candidates')} candidates with fresh NAVs)."
        ),
    }


def pros_cons(pick: dict) -> tuple[list[str], list[str]]:
    """Numbered pros/cons for one pick. Every figure is quoted from the
    pick's own stats — no adjectives without numbers."""
    pros, cons = [], []
    kind, role = pick.get("kind"), pick.get("role")
    if kind == "mf":
        cagr = pick.get("cagr3Y")
        if cagr is not None:
            pros.append(
                f"3Y CAGR {cagr:.1f}% — highest risk-adjusted return "
                f"among the scanned {pick.get('category')} Growth plans.")
        sip = pick.get("sip3Y") or {}
        if sip.get("value") is not None:
            pros.append(
                f"₹10,000/month SIP for 3 years grew to "
                f"₹{_inr(sip['value'])} (+{sip.get('gainPct', 0):.1f}%).")
        r1y = pick.get("return1Y")
        if r1y is not None and r1y < 0:
            cons.append(
                f"1Y return {r1y:.1f}% — the 3Y headline hides a weak "
                f"recent year.")
        dd = pick.get("maxDrawdownPct")
        if dd is not None and dd < 0:
            bottom = 100000 * (1 + dd / 100)
            cons.append(
                f"Fell {abs(dd):.1f}% peak-to-trough in the last 3 "
                f"years — a ₹1 lakh lump sum would have shown "
                f"₹{_inr(bottom)} at the bottom.")
        cons.append(
            "Direct plan shown — Regular plans return less after "
            "distributor commission.")
        cons.append(
            "Equity pick — fits 5+ year horizons only; don't use money "
            "needed sooner.")
    elif kind == "etf" and role == "index_etf":
        pros.append(
            "One fund covering a broad market index — instant "
            "diversification, no fund-manager risk.")
        score = pick.get("score")
        if score is not None and score >= 20:
            pros.append(
                f"Trend score {score:.0f} ({pick.get('verdict')}) — "
                f"momentum is currently positive.")
        elif score is not None and score <= -20:
            cons.append(
                f"Trend score {score:.0f} ({pick.get('verdict')}) — "
                f"momentum is currently weak, so treat this as a "
                f"long-term core, not a timing call.")
        cons.append("Falls with the market — no protection in a correction.")
    elif kind == "etf" and role == "gold_etf":
        pros.append(
            "Moves differently from stocks — often steadies the "
            "portfolio when equities fall.")
        cons.append(
            "No income — no dividends or interest; can go through long "
            "dull stretches.")
        cons.append(
            "Gold prices swing too — this is a hedge, not a safe deposit.")
    elif kind == "etf" and role == "liquid":
        pros.append(
            "Stability first — value barely fluctuates; the right "
            "parking place for money needed soon.")
        cons.append(
            "Returns roughly track inflation at best — this slice is "
            "for safety, not growth.")
    return pros, cons


def build_portfolio(profile: str) -> dict | None:
    if profile not in PROFILES:
        return None
    return cached(f"advisor:{profile}", FINDER_TTL,
                   lambda: _build_portfolio(profile))


def _build_portfolio(profile: str) -> dict | None:
    meta = PROFILES[profile]
    slots = meta["slots"]
    etf_roles = [r for r, _ in slots if r in ("index_etf", "gold_etf", "liquid")]
    mf_roles = [(r, MF_CATEGORY[r]) for r, _ in slots if r in MF_CATEGORY]
    etf_rows = scan_universe("etf") if etf_roles else []
    mf_picks: dict[str, dict | None] = {}
    if mf_roles:
        with ThreadPoolExecutor(max_workers=3) as pool:
            for role, pick in zip(
                    [r for r, _ in mf_roles],
                    pool.map(lambda rc: pick_mf(rc[1]), mf_roles)):
                mf_picks[role] = pick
    picks = []
    for role, pct in slots:
        if role in MF_CATEGORY:
            raw = mf_picks.get(role)
        else:
            raw = pick_etf(role, etf_rows)
        if not raw:
            continue
        raw = dict(raw)
        raw["role"] = role
        raw["job"] = JOBS[role]
        raw["allocationPct"] = pct
        raw["pros"], raw["cons"] = pros_cons(raw)
        picks.append(raw)
    if not picks:
        return None
    total = sum(p["allocationPct"] for p in picks)
    return {
        "profile": profile,
        "profileLabel": meta["label"],
        "profileLine": meta["line"],
        "picks": picks,
        "totalPct": total,
        "incomplete": total != 100,
        "incompleteNote": (
            "One or more picks could not be loaded, so the percentages "
            "below don't add up to 100 yet — retry later for the full mix."
        ) if total != 100 else None,
        "source": "live",
        "method": (
            "ETF index slot: broad-index ETFs first, then highest trend "
            "score. Gold slot fixed by role. Liquid slot picked for "
            "stability with its trend verdict suppressed. Mutual-fund "
            "slots: best risk-adjusted return (3Y CAGR / volatility) "
            "among each category's top leaders, Direct Growth plans "
            "only. Rankings use trailing returns to the latest NAV date."
        ),
        "coverageNote": (
            "Mutual-fund picks come from the first 20 matching Growth "
            "plans per category with fresh NAVs — not the whole "
            "category. Shut-down or merged funds are excluded, so "
            "history looks rosier than the average investor's "
            "experience."
        ),
        "missingDataNote": (
            "Expense ratio, fund-manager tenure, holdings overlap, exit "
            "loads and the SEBI riskometer are not available from the "
            "data sources used here — check them before investing. "
            "Expense ratio is not shown; Regular plans cost more than "
            "the Direct plans shown."
        ),
        "keySentence": KEY_SENTENCE,
        "disclaimer": DISCLAIMER,
    }
