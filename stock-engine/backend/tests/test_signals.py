from app.indicators.engine import compute_all
from app.signals.levels import pivot_points, support_resistance
from app.signals.scoring import collect_votes, composite_score, confidence_for, verdict_for
from app.signals.trade_plan import build_trade_plan


def test_uptrend_scores_bullish(uptrend):
    enriched = compute_all(uptrend)
    votes = collect_votes(enriched)
    score = composite_score(votes)
    assert score > 20, f"expected bullish score, got {score}"
    assert verdict_for(score) in ("Buy", "Strong Buy")


def test_downtrend_scores_bearish(downtrend):
    enriched = compute_all(downtrend)
    votes = collect_votes(enriched)
    score = composite_score(votes)
    assert score < -20, f"expected bearish score, got {score}"
    assert verdict_for(score) in ("Sell", "Strong Sell")


def test_votes_have_reasons(uptrend):
    votes = collect_votes(compute_all(uptrend))
    assert len(votes) >= 10
    for v in votes:
        assert v["reason"] and len(v["reason"]) > 10
        assert -2 <= v["vote"] <= 2
        assert v["state"] in ("bullish", "bearish", "neutral")


def test_verdict_boundaries():
    assert verdict_for(75) == "Strong Buy"
    assert verdict_for(30) == "Buy"
    assert verdict_for(0) == "Hold"
    assert verdict_for(-30) == "Sell"
    assert verdict_for(-75) == "Strong Sell"


def test_confidence_range(uptrend, sideways):
    for df in (uptrend, sideways):
        votes = collect_votes(compute_all(df))
        score = composite_score(votes)
        assert 0 <= confidence_for(votes, score) <= 100


def test_pivot_ordering(uptrend):
    p = pivot_points(uptrend)
    assert p["s3"] < p["s2"] < p["s1"] < p["pivot"] < p["r1"] < p["r2"] < p["r3"]


def test_support_resistance_sides(sideways):
    lvl = support_resistance(sideways)
    price = float(sideways["Close"].iloc[-1])
    assert all(z["level"] < price for z in lvl["supports"])
    assert all(z["level"] >= price for z in lvl["resistances"])
    # nearest-first ordering
    sup = [z["level"] for z in lvl["supports"]]
    assert sup == sorted(sup, reverse=True)


def test_trade_plan_buy_structure(uptrend):
    enriched = compute_all(uptrend)
    lvl = support_resistance(uptrend)
    plan = build_trade_plan(enriched, "Buy", lvl)
    assert plan["action"] in ("BUY", "BUY_ON_DIP")
    entry_low, entry_high = plan["entryZone"]
    entry = (entry_low + entry_high) / 2
    assert plan["stopLoss"] < entry < plan["target1"] < plan["target2"]
    assert plan["riskReward"] > 0


def test_trade_plan_sell_structure(downtrend):
    enriched = compute_all(downtrend)
    lvl = support_resistance(downtrend)
    plan = build_trade_plan(enriched, "Sell", lvl)
    assert plan["action"] == "AVOID_OR_EXIT"
    assert plan["notes"]


def test_full_analysis_demo_mode(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "on")
    import importlib

    from app import config
    importlib.reload(config)
    from app.data import fetcher
    importlib.reload(fetcher)
    from app.signals import analysis
    importlib.reload(analysis)

    report = analysis._analyze("RELIANCE")
    assert report is not None
    assert report["verdict"] in ("Strong Buy", "Buy", "Hold", "Sell", "Strong Sell")
    assert report["tradePlan"]["action"] is not None
    assert len(report["votes"]) >= 10
    assert report["dataSource"] == "demo"
    assert report["disclaimer"]
