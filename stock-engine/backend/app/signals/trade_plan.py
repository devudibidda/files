"""Trade plan generation: entry zone, stop-loss, targets, risk-reward."""
import math

import pandas as pd


def position_sizing(entry: float, stop: float, account_size: float, risk_pct: float) -> dict | None:
    """How many shares for a fixed account risk.

    risk_amount = account_size * risk_pct / 100, spread over the per-share
    risk (entry - stop). Shares are floored so the risk cap is never exceeded.
    Returns None when the plan has no usable long entry/stop.
    """
    if entry is None or stop is None:
        return None
    if account_size is None or account_size <= 0 or risk_pct is None or risk_pct <= 0:
        return None
    risk_per_share = entry - stop
    if risk_per_share <= 0:
        return None
    risk_amount = account_size * risk_pct / 100.0
    shares = math.floor(risk_amount / risk_per_share)
    if shares <= 0:
        return None
    capital = round(shares * entry, 2)
    return {
        "shares": shares,
        "riskPerShare": round(risk_per_share, 2),
        "riskAmount": round(risk_amount, 2),
        "capitalRequired": capital,
        "pctOfAccount": round(capital / account_size * 100, 1),
    }


def build_trade_plan(
    enriched: pd.DataFrame,
    verdict: str,
    levels: dict,
    account_size: float = 100000,
    risk_pct: float = 1.0,
) -> dict:
    last = enriched.iloc[-1]
    price = float(last["Close"])
    atr = float(last["ATR14"]) if pd.notna(last["ATR14"]) else price * 0.02
    ema20 = float(last["EMA20"]) if pd.notna(last["EMA20"]) else price

    supports = [z["level"] for z in levels.get("supports", [])]
    resistances = [z["level"] for z in levels.get("resistances", [])]
    nearest_support = supports[0] if supports else None
    nearest_resistance = resistances[0] if resistances else None

    plan: dict = {
        "action": None,
        "entryZone": None,
        "stopLoss": None,
        "target1": None,
        "target2": None,
        "riskReward": None,
        "positionSizing": None,
        "notes": [],
    }

    if verdict in ("Strong Buy", "Buy"):
        # Entry: at market if price is near support/EMA20, else wait for a pullback
        pullback_ref = max(
            [x for x in (nearest_support, ema20) if x is not None and x < price],
            default=None,
        )
        if pullback_ref is not None and (price - pullback_ref) / price <= 0.02:
            entry_low, entry_high = round(pullback_ref, 2), round(price, 2)
            plan["action"] = "BUY"
            plan["notes"].append(
                "Price is within 2% of its nearest demand zone — entering near current levels is reasonable."
            )
        elif pullback_ref is not None:
            entry_low, entry_high = round(pullback_ref * 0.995, 2), round(pullback_ref * 1.01, 2)
            plan["action"] = "BUY_ON_DIP"
            plan["notes"].append(
                f"Price is extended above support — a pullback entry near ₹{round(pullback_ref, 2)} "
                f"(20-EMA / demand zone) offers better risk-reward."
            )
        else:
            entry_low, entry_high = round(price * 0.99, 2), round(price, 2)
            plan["action"] = "BUY"

        entry = (entry_low + entry_high) / 2

        # Stop: 2×ATR below entry, tightened to just under the swing low when closer
        atr_stop = entry - 2 * atr
        swing_stop = nearest_support * 0.99 if nearest_support and nearest_support < entry else None
        stop = max([s for s in (atr_stop, swing_stop) if s is not None])
        risk = entry - stop
        if risk <= 0:
            stop = entry - 2 * atr
            risk = 2 * atr

        t1, t2 = entry + 1.5 * risk, entry + 2.5 * risk
        plan.update({
            "entryZone": [entry_low, entry_high],
            "stopLoss": round(stop, 2),
            "target1": round(t1, 2),
            "target2": round(t2, 2),
            "riskReward": round((t1 - entry) / risk, 2),
        })
        plan["positionSizing"] = position_sizing(entry, stop, account_size, risk_pct)
        if nearest_resistance and nearest_resistance < t1:
            plan["notes"].append(
                f"Caution: resistance at ₹{nearest_resistance} sits before target 1 — "
                "consider booking partial profits there."
            )
        if plan["riskReward"] < 1.5:
            plan["notes"].append("Risk-reward below 1.5 — setup quality is marginal; size down or skip.")

    elif verdict in ("Sell", "Strong Sell"):
        plan["action"] = "AVOID_OR_EXIT"
        exit_trigger = nearest_support if nearest_support else round(price - 2 * atr, 2)
        plan["stopLoss"] = round(nearest_resistance * 1.01, 2) if nearest_resistance else round(price + 2 * atr, 2)
        plan["notes"].append(
            "Technicals are bearish — fresh long entries are not favored."
        )
        plan["notes"].append(
            f"For existing holders: a close below support at ₹{round(exit_trigger, 2)} would confirm further downside; "
            f"a recovery above ₹{plan['stopLoss']} would negate the bearish setup."
        )

    else:  # Hold
        plan["action"] = "WAIT"
        if nearest_support and nearest_resistance:
            plan["entryZone"] = [round(nearest_support, 2), round(nearest_support * 1.01, 2)]
            plan["notes"].append(
                f"Signals are mixed — the range is roughly ₹{nearest_support} (support) to "
                f"₹{nearest_resistance} (resistance). Wait for a decisive break, or accumulate near support."
            )
        else:
            plan["notes"].append("Signals are mixed — wait for a clearer trend before committing capital.")

    return plan
