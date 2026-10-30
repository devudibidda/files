"""Tests for the My First Portfolio finder (pure logic + stubbed picks)."""

import pytest

from app import advisor
from app.advisor import PROFILES, build_portfolio, pick_etf, pick_mf, profile_for, pros_cons


def test_profile_mapping():
    assert profile_for("short", "panic") == "conservative"
    assert profile_for("short", "invest") == "conservative"
    assert profile_for("medium", "panic") == "conservative"
    assert profile_for("medium", "hold") == "balanced"
    assert profile_for("medium", "invest") == "balanced"
    assert profile_for("long", "panic") == "conservative"
    assert profile_for("long", "hold") == "balanced"
    assert profile_for("long", "invest") == "growth"


def test_allocations_sum_to_100_and_no_small_cap():
    for pid, meta in PROFILES.items():
        assert sum(p for _, p in meta["slots"]) == 100, pid
        assert len(meta["slots"]) <= 4, pid
        roles = [r for r, _ in meta["slots"]]
        assert "small_cap_mf" not in roles, pid
    assert "mid_cap_mf" in [r for r, _ in PROFILES["growth"]["slots"]]
    assert "mid_cap_mf" not in [r for r, _ in PROFILES["conservative"]["slots"]]


def test_mf_pros_cons_quote_numbers():
    pick = {
        "kind": "mf", "role": "flexi_cap_mf", "category": "flexi-cap",
        "cagr3Y": 16.94, "return1Y": -3.2, "volatilityPct": 15.4,
        "maxDrawdownPct": -21.44,
        "sip3Y": {"invested": 360000, "value": 412749, "gainPct": 14.65},
    }
    pros, cons = pros_cons(pick)
    assert any("16.9%" in p for p in pros)
    assert any("4,12,749" in p for p in pros)
    assert any("weak recent year" in c for c in cons)
    assert any("78,560" in c for c in cons)
    assert any("Direct plan" in c for c in cons)
    assert any("5+ year" in c for c in cons)


def test_liquid_verdict_suppressed_and_gold_honest():
    rows = [
        {"symbol": "LIQUIDBEES", "name": "Nippon India Liquid BeES",
         "sector": "Debt ETF", "score": -62, "verdict": "Strong Sell", "source": "live"},
        {"symbol": "GOLDBEES", "name": "Nippon India Gold BeES",
         "sector": "Gold ETF", "score": 71, "verdict": "Strong Buy", "source": "live"},
    ]
    liquid = pick_etf("liquid", rows)
    assert liquid["verdict"] is None
    assert "Not rated" in liquid["ratingNote"]
    pros, cons = pros_cons({**liquid, "role": "liquid"})
    assert any("barely fluctuates" in p for p in pros)
    gold = pick_etf("gold_etf", rows)
    pros, cons = pros_cons({**gold, "role": "gold_etf"})
    assert any("No income" in c for c in cons)


def test_index_slot_prefers_broad_names():
    rows = [
        {"symbol": "BANKBEES", "name": "Nippon India Nifty Bank BeES",
         "sector": "Index ETF", "score": 90, "verdict": "Strong Buy", "source": "live"},
        {"symbol": "NIFTYBEES", "name": "Nippon India Nifty 50 BeES",
         "sector": "Index ETF", "score": 40, "verdict": "Buy", "source": "live"},
    ]
    assert pick_etf("index_etf", rows)["symbol"] == "NIFTYBEES"


def test_build_portfolio_with_stubbed_picks(monkeypatch):
    def fake_etf(role, rows=None):
        return {"kind": "etf", "symbol": "X", "name": "X ETF",
                "source": "live", "score": 50, "verdict": "Buy",
                "ratingNote": None, "selectionNote": "stub"}

    def fake_mf(category):
        return {"kind": "mf", "schemeCode": 1, "name": "Stub Fund",
                "category": category, "return1Y": 5.0, "cagr3Y": 12.0,
                "volatilityPct": 10.0, "maxDrawdownPct": -8.0,
                "sip3Y": {"value": 380000, "gainPct": 5.5},
                "selectionNote": "stub"}

    monkeypatch.setattr(advisor, "pick_etf", fake_etf)
    monkeypatch.setattr(advisor, "pick_mf", fake_mf)
    monkeypatch.setattr(advisor, "scan_universe", lambda type_=None: [])
    # Bypass the 24h cache so stubs are used fresh.
    monkeypatch.setattr(advisor, "cached", lambda key, ttl, fn: fn())
    result = build_portfolio("balanced")
    assert result["totalPct"] == 100
    assert not result["incomplete"]
    assert [p["role"] for p in result["picks"]] == [
        "index_etf", "flexi_cap_mf", "large_cap_mf", "gold_etf"]
    for p in result["picks"]:
        assert p["job"] and p["pros"] and p["cons"]
    assert "not personal investment advice" in result["disclaimer"]


def test_build_portfolio_unknown_profile():
    assert build_portfolio("nope") is None
