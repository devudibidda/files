"""Tests for the Oct 30 audit features: position sizing, relative strength, backtest."""
import pandas as pd

from app.indicators.engine import compute_all
from app.signals.analysis import relative_strength
from app.signals.backtest import _horizon_stats, _walk
from app.signals.levels import support_resistance
from app.signals.trade_plan import build_trade_plan, position_sizing


def test_position_sizing_exact():
    s = position_sizing(entry=1000, stop=950, account_size=100000, risk_pct=1.0)
    assert s["riskPerShare"] == 50
    assert s["riskAmount"] == 1000
    assert s["shares"] == 20
    assert s["capitalRequired"] == 20000
    assert s["pctOfAccount"] == 20.0


def test_position_sizing_floors_shares():
    s = position_sizing(entry=100, stop=70, account_size=100000, risk_pct=1.0)
    assert s["shares"] == 33  # floor(1000 / 30), never exceeding the risk cap
    assert s["shares"] * 30 <= 1000


def test_position_sizing_invalid():
    assert position_sizing(100, 100, 100000, 1.0) is None  # no per-share risk
    assert position_sizing(100, 110, 100000, 1.0) is None  # stop above entry
    assert position_sizing(100, 90, 0, 1.0) is None
    assert position_sizing(100, 90, 100000, 0) is None
    assert position_sizing(100, 50, 1000, 1.0) is None  # risk cap buys 0 shares


def test_trade_plan_carries_sizing(uptrend):
    enriched = compute_all(uptrend)
    lvl = support_resistance(uptrend)
    plan = build_trade_plan(enriched, "Buy", lvl, account_size=100000, risk_pct=1.0)
    assert plan["positionSizing"] is not None
    assert plan["positionSizing"]["shares"] > 0


def test_relative_strength_structure(uptrend):
    # NIFTY flat while the stock trends up: outperformance must be positive.
    nifty = uptrend.copy()
    nifty["Close"] = 100.0
    nifty["High"] = 101.0
    nifty["Low"] = 99.0
    rs = relative_strength(uptrend, nifty)
    assert rs is not None
    # 250-day fixture: 1M/3M available, 1Y needs >252 rows so it is skipped
    assert set(rs.keys()) == {"1M", "3M"}
    for v in rs.values():
        assert abs(v["outperformance"] - (v["stock"] - v["nifty"])) < 0.15
        assert v["outperformance"] > 0


def test_relative_strength_missing():
    assert relative_strength(None, None) is None
    short = pd.DataFrame(
        {"Open": [1.0], "High": [1.0], "Low": [1.0], "Close": [1.0], "Volume": [1.0]}
    )
    assert relative_strength(short, short) is None


def test_backtest_walk_uptrend(uptrend):
    enriched = compute_all(uptrend)
    signals = _walk(enriched, uptrend)
    assert len(signals) > 0, "steady uptrend should produce Buy signals"
    for s in signals:
        assert set(s.keys()) == {10, 20}
    stats = _horizon_stats(signals, 20)
    assert 0 <= stats["winRate"] <= 100
    assert stats["avgReturn"] > 0, "uptrend forward returns should average positive"


def test_backtest_walk_downtrend(downtrend):
    enriched = compute_all(downtrend)
    signals = _walk(enriched, downtrend)
    assert len(signals) == 0, "steady downtrend should not produce Buy signals"


def test_horizon_stats_empty():
    assert _horizon_stats([], 10) == {"winRate": None, "avgReturn": None}
