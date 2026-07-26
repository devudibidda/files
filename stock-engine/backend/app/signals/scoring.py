"""Weighted confluence scoring.

Every indicator casts a vote from -2 (strongly bearish) to +2 (strongly
bullish) with a weight — trend indicators weigh more than oscillators.
The normalized composite score (-100..+100) maps to a verdict.

Each vote also carries a plain-English reason so the UI can explain itself.
"""
import pandas as pd


def _vote(name, value, vote, weight, reason):
    state = "bullish" if vote > 0 else "bearish" if vote < 0 else "neutral"
    return {
        "indicator": name,
        "value": value,
        "vote": vote,
        "weight": weight,
        "state": state,
        "reason": reason,
    }


def collect_votes(enriched: pd.DataFrame) -> list[dict]:
    last = enriched.iloc[-1]
    prev = enriched.iloc[-2] if len(enriched) > 1 else last
    votes: list[dict] = []

    close = float(last["Close"])

    def ok(*cols):
        return all(pd.notna(last[c]) for c in cols)

    # --- Long-term trend: price vs EMA200 (weight 1.5) ---
    if ok("EMA200"):
        ema200 = float(last["EMA200"])
        dist = (close - ema200) / ema200 * 100
        if dist > 1:
            votes.append(_vote("EMA 200", round(ema200, 2), 2, 1.5,
                               f"Price is {dist:.1f}% above the 200-EMA — long-term uptrend intact."))
        elif dist < -1:
            votes.append(_vote("EMA 200", round(ema200, 2), -2, 1.5,
                               f"Price is {abs(dist):.1f}% below the 200-EMA — long-term trend is down."))
        else:
            votes.append(_vote("EMA 200", round(ema200, 2), 0, 1.5,
                               "Price is hovering at the 200-EMA — long-term trend is being decided here."))

    # --- Medium trend: price vs EMA50 and its slope (weight 1.0) ---
    if ok("EMA50"):
        ema50, ema50_prev = float(last["EMA50"]), float(prev["EMA50"])
        rising = ema50 > ema50_prev
        if close > ema50 and rising:
            votes.append(_vote("EMA 50", round(ema50, 2), 2, 1.0,
                               "Price is above a rising 50-EMA — healthy medium-term uptrend."))
        elif close > ema50:
            votes.append(_vote("EMA 50", round(ema50, 2), 1, 1.0,
                               "Price is above the 50-EMA, though the average has flattened."))
        elif close < ema50 and not rising:
            votes.append(_vote("EMA 50", round(ema50, 2), -2, 1.0,
                               "Price is below a falling 50-EMA — medium-term pressure persists."))
        else:
            votes.append(_vote("EMA 50", round(ema50, 2), -1, 1.0,
                               "Price slipped below the 50-EMA — medium-term trend weakening."))

    # --- Golden/death cross context: SMA50 vs SMA200 (weight 1.0) ---
    if ok("SMA50", "SMA200"):
        s50, s200 = float(last["SMA50"]), float(last["SMA200"])
        if s50 > s200:
            votes.append(_vote("SMA 50/200 cross", round(s50 - s200, 2), 2, 1.0,
                               "50-SMA above 200-SMA (golden-cross regime) — structural bull phase."))
        else:
            votes.append(_vote("SMA 50/200 cross", round(s50 - s200, 2), -2, 1.0,
                               "50-SMA below 200-SMA (death-cross regime) — structural bear phase."))

    # --- Supertrend (weight 1.5) ---
    if ok("ST_DIR", "ST_LINE"):
        st_dir = int(last["ST_DIR"])
        st_line = round(float(last["ST_LINE"]), 2)
        if st_dir == 1:
            votes.append(_vote("Supertrend (10,3)", st_line, 2, 1.5,
                               f"Supertrend is bullish with trailing support at ₹{st_line}."))
        else:
            votes.append(_vote("Supertrend (10,3)", st_line, -2, 1.5,
                               f"Supertrend is bearish with overhead resistance at ₹{st_line}."))

    # --- MACD (weight 1.2) ---
    if ok("MACD", "MACD_SIGNAL", "MACD_HIST"):
        m, s, h = float(last["MACD"]), float(last["MACD_SIGNAL"]), float(last["MACD_HIST"])
        h_prev = float(prev["MACD_HIST"]) if pd.notna(prev["MACD_HIST"]) else h
        if m > s and h > h_prev:
            votes.append(_vote("MACD (12,26,9)", round(m, 2), 2, 1.2,
                               "MACD is above its signal line with a growing histogram — momentum building."))
        elif m > s:
            votes.append(_vote("MACD (12,26,9)", round(m, 2), 1, 1.2,
                               "MACD is above its signal line but momentum is fading."))
        elif m < s and h < h_prev:
            votes.append(_vote("MACD (12,26,9)", round(m, 2), -2, 1.2,
                               "MACD is below its signal line and falling — bearish momentum."))
        else:
            votes.append(_vote("MACD (12,26,9)", round(m, 2), -1, 1.2,
                               "MACD is below its signal line, though downside momentum is easing."))

    # --- ADX trend strength (weight 0.8) ---
    if ok("ADX14", "PLUS_DI", "MINUS_DI"):
        a, pdi, mdi = float(last["ADX14"]), float(last["PLUS_DI"]), float(last["MINUS_DI"])
        if a >= 25 and pdi > mdi:
            votes.append(_vote("ADX (14)", round(a, 1), 2, 0.8,
                               f"ADX at {a:.0f} confirms a strong trend, and +DI leads — buyers in control."))
        elif a >= 25 and mdi > pdi:
            votes.append(_vote("ADX (14)", round(a, 1), -2, 0.8,
                               f"ADX at {a:.0f} confirms a strong trend, and -DI leads — sellers in control."))
        elif a >= 20:
            direction = 1 if pdi > mdi else -1
            votes.append(_vote("ADX (14)", round(a, 1), direction, 0.8,
                               f"ADX at {a:.0f} shows a developing trend."))
        else:
            votes.append(_vote("ADX (14)", round(a, 1), 0, 0.8,
                               f"ADX at {a:.0f} — no meaningful trend; expect range-bound movement."))

    # --- Ichimoku cloud (weight 1.0) ---
    if ok("ICHI_A", "ICHI_B"):
        top = max(float(last["ICHI_A"]), float(last["ICHI_B"]))
        bottom = min(float(last["ICHI_A"]), float(last["ICHI_B"]))
        if close > top:
            votes.append(_vote("Ichimoku Cloud", round(top, 2), 2, 1.0,
                               "Price is trading above the Ichimoku cloud — trend support below."))
        elif close < bottom:
            votes.append(_vote("Ichimoku Cloud", round(bottom, 2), -2, 1.0,
                               "Price is trading below the Ichimoku cloud — overhead supply zone."))
        else:
            votes.append(_vote("Ichimoku Cloud", round(top, 2), 0, 1.0,
                               "Price is inside the Ichimoku cloud — indecision zone."))

    # --- RSI (weight 1.0) ---
    if ok("RSI14"):
        r = float(last["RSI14"])
        if r >= 70:
            votes.append(_vote("RSI (14)", round(r, 1), -2, 1.0,
                               f"RSI at {r:.0f} is overbought — chasing here has poor risk-reward."))
        elif r >= 55:
            votes.append(_vote("RSI (14)", round(r, 1), 1, 1.0,
                               f"RSI at {r:.0f} shows healthy momentum without being overbought."))
        elif r > 45:
            votes.append(_vote("RSI (14)", round(r, 1), 0, 1.0,
                               f"RSI at {r:.0f} is neutral."))
        elif r > 30:
            votes.append(_vote("RSI (14)", round(r, 1), -1, 1.0,
                               f"RSI at {r:.0f} shows weak momentum."))
        else:
            votes.append(_vote("RSI (14)", round(r, 1), 2, 1.0,
                               f"RSI at {r:.0f} is oversold — mean-reversion bounce zone."))

    # --- Stochastic (weight 0.6) ---
    if ok("STOCH_K", "STOCH_D"):
        k, d = float(last["STOCH_K"]), float(last["STOCH_D"])
        if k <= 20:
            votes.append(_vote("Stochastic (14,3,3)", round(k, 1), 2, 0.6,
                               f"Stochastic %K at {k:.0f} is oversold — watch for a reversal trigger."))
        elif k >= 80:
            votes.append(_vote("Stochastic (14,3,3)", round(k, 1), -1, 0.6,
                               f"Stochastic %K at {k:.0f} is overbought."))
        elif k > d:
            votes.append(_vote("Stochastic (14,3,3)", round(k, 1), 1, 0.6,
                               "%K has crossed above %D — short-term momentum turning up."))
        else:
            votes.append(_vote("Stochastic (14,3,3)", round(k, 1), -1, 0.6,
                               "%K is below %D — short-term momentum points down."))

    # --- Bollinger position (weight 0.7) ---
    if ok("BB_UPPER", "BB_LOWER", "BB_MID"):
        up, lo, mid = float(last["BB_UPPER"]), float(last["BB_LOWER"]), float(last["BB_MID"])
        if close <= lo:
            votes.append(_vote("Bollinger (20,2)", round(lo, 2), 2, 0.7,
                               "Price is at/below the lower Bollinger band — statistically stretched down."))
        elif close >= up:
            votes.append(_vote("Bollinger (20,2)", round(up, 2), -1, 0.7,
                               "Price is riding the upper Bollinger band — extended in the short term."))
        elif close > mid:
            votes.append(_vote("Bollinger (20,2)", round(mid, 2), 1, 0.7,
                               "Price is holding above the Bollinger midline."))
        else:
            votes.append(_vote("Bollinger (20,2)", round(mid, 2), -1, 0.7,
                               "Price is below the Bollinger midline."))

    # --- Volume confirmation (weight 0.8) ---
    if ok("VOL_SMA20") and float(last["VOL_SMA20"]) > 0:
        ratio = float(last["Volume"]) / float(last["VOL_SMA20"])
        green = close >= float(last["Open"])
        if ratio >= 1.5 and green:
            votes.append(_vote("Volume", round(ratio, 2), 2, 0.8,
                               f"Volume is {ratio:.1f}× its 20-day average on an up move — strong participation."))
        elif ratio >= 1.5 and not green:
            votes.append(_vote("Volume", round(ratio, 2), -2, 0.8,
                               f"Volume is {ratio:.1f}× average on a down move — distribution pressure."))
        elif ratio >= 1.0:
            votes.append(_vote("Volume", round(ratio, 2), 1 if green else -1, 0.8,
                               "Volume is around average — no strong conviction either way."))
        else:
            votes.append(_vote("Volume", round(ratio, 2), 0, 0.8,
                               "Volume is below average — moves here carry less weight."))

    # --- Chaikin Money Flow (weight 0.6) ---
    if ok("CMF20"):
        c = float(last["CMF20"])
        if c > 0.1:
            votes.append(_vote("Chaikin Money Flow", round(c, 3), 2, 0.6,
                               f"CMF at {c:.2f} — sustained buying pressure / accumulation."))
        elif c > 0:
            votes.append(_vote("Chaikin Money Flow", round(c, 3), 1, 0.6,
                               "CMF is mildly positive — buyers have a slight edge."))
        elif c > -0.1:
            votes.append(_vote("Chaikin Money Flow", round(c, 3), -1, 0.6,
                               "CMF is mildly negative — sellers have a slight edge."))
        else:
            votes.append(_vote("Chaikin Money Flow", round(c, 3), -2, 0.6,
                               f"CMF at {c:.2f} — persistent selling / distribution."))

    # --- VWAP20 (weight 0.5) ---
    if ok("VWAP20"):
        vw = float(last["VWAP20"])
        if close > vw:
            votes.append(_vote("VWAP (20d)", round(vw, 2), 1, 0.5,
                               "Price is above the 20-day VWAP — average buyer is in profit."))
        else:
            votes.append(_vote("VWAP (20d)", round(vw, 2), -1, 0.5,
                               "Price is below the 20-day VWAP — average recent buyer is underwater."))

    return votes


def composite_score(votes: list[dict]) -> float:
    """Normalize weighted votes to -100..+100."""
    if not votes:
        return 0.0
    total = sum(v["vote"] * v["weight"] for v in votes)
    max_total = sum(2 * v["weight"] for v in votes)
    return round(total / max_total * 100, 1) if max_total else 0.0


def verdict_for(score: float) -> str:
    if score >= 60:
        return "Strong Buy"
    if score >= 20:
        return "Buy"
    if score > -20:
        return "Hold"
    if score > -60:
        return "Sell"
    return "Strong Sell"


def confidence_for(votes: list[dict], score: float) -> int:
    """Confidence = agreement between indicators (0-100).

    High |score| with few dissenting votes → high confidence.
    """
    if not votes:
        return 0
    direction = 1 if score >= 0 else -1
    weight_total = sum(v["weight"] for v in votes)
    agreeing = sum(v["weight"] for v in votes if v["vote"] * direction > 0)
    agreement = agreeing / weight_total if weight_total else 0
    return int(round(min(100, abs(score) * 0.5 + agreement * 50)))
