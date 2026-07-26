"""Price levels: classic pivot points and swing-based support/resistance zones."""
import numpy as np
import pandas as pd


def pivot_points(df: pd.DataFrame) -> dict:
    """Classic floor-trader pivots from the latest completed candle."""
    last = df.iloc[-1]
    h, l, c = float(last["High"]), float(last["Low"]), float(last["Close"])
    p = (h + l + c) / 3
    return {
        "pivot": round(p, 2),
        "r1": round(2 * p - l, 2),
        "s1": round(2 * p - h, 2),
        "r2": round(p + (h - l), 2),
        "s2": round(p - (h - l), 2),
        "r3": round(h + 2 * (p - l), 2),
        "s3": round(l - 2 * (h - p), 2),
    }


def _swing_points(series: pd.Series, window: int, find_high: bool) -> list[float]:
    """Local extrema: bar is a swing high/low if it is the extreme of ±window bars."""
    values = series.to_numpy()
    points = []
    for i in range(window, len(values) - window):
        segment = values[i - window : i + window + 1]
        if find_high and values[i] == segment.max():
            points.append(float(values[i]))
        elif not find_high and values[i] == segment.min():
            points.append(float(values[i]))
    return points


def _cluster(levels: list[float], tolerance: float) -> list[dict]:
    """Merge nearby levels into zones; strength = number of touches."""
    if not levels:
        return []
    levels = sorted(levels)
    zones: list[list[float]] = [[levels[0]]]
    for lv in levels[1:]:
        if lv - zones[-1][-1] <= tolerance:
            zones[-1].append(lv)
        else:
            zones.append([lv])
    return [
        {"level": round(float(np.mean(z)), 2), "strength": len(z)}
        for z in zones
    ]


def support_resistance(df: pd.DataFrame, lookback: int = 180, window: int = 5) -> dict:
    """Swing-based support/resistance zones around the current price."""
    recent = df.tail(lookback)
    price = float(recent["Close"].iloc[-1])
    # zone tolerance: ~1.2% of price
    tolerance = price * 0.012

    highs = _swing_points(recent["High"], window, find_high=True)
    lows = _swing_points(recent["Low"], window, find_high=False)
    zones = _cluster(highs + lows, tolerance)

    supports = sorted(
        [z for z in zones if z["level"] < price],
        key=lambda z: z["level"], reverse=True,
    )[:4]
    resistances = sorted(
        [z for z in zones if z["level"] >= price],
        key=lambda z: z["level"],
    )[:4]
    return {"supports": supports, "resistances": resistances}
