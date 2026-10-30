"""Tests for mutual fund NAV math (fixture series, no network)."""
from datetime import timedelta

import pandas as pd

from app.mf import (
    _is_growth_plan,
    _max_drawdown,
    _returns,
    _sip,
    _volatility,
    base_name,
    matches_category,
)


def _series(navs, start="2022-01-03"):
    idx = pd.bdate_range(start, periods=len(navs))
    return [(d.date(), float(v)) for d, v in zip(idx, navs)]


def test_returns_rising_series():
    nav = _series([100 * (1.001 ** i) for i in range(800)])
    r = _returns(nav)
    assert set(r.keys()) == {"1M", "3M", "6M", "1Y", "3Y"}
    assert 25 < r["1Y"]["returnPct"] < 32  # 1.001^252 - 1
    assert r["1Y"]["cagrPct"] > r["1Y"]["returnPct"]  # annualized over ~352 days
    assert r["1M"]["cagrPct"] is None  # short horizons stay absolute
    assert 25 < r["3Y"]["cagrPct"] < 35


def test_returns_flat_series():
    nav = _series([100.0] * 300)
    r = _returns(nav)
    assert r["1Y"]["returnPct"] == 0.0
    assert r["1M"]["returnPct"] == 0.0


def test_volatility_flat_is_zero():
    assert _volatility(_series([100.0] * 300)) == 0.0


def test_volatility_noisy_in_range():
    import numpy as np

    rng = np.random.RandomState(5)
    navs = 100 * (1 + rng.normal(0, 0.01, 300)).cumprod()
    v = _volatility(_series(list(navs)))
    assert 5 < v < 40  # ~1% daily noise -> ~16% annualized


def test_max_drawdown_known_dip():
    navs = [100.0] * 50 + [200.0] * 50 + [120.0] * 50 + [200.0] * 50
    assert _max_drawdown(_series(navs)) == -40.0


def test_sip_flat_nav_no_gain():
    nav = _series([100.0] * 800)
    s = _sip(nav)
    assert s["1Y"]["invested"] == 120000
    assert s["1Y"]["value"] == 120000
    assert s["1Y"]["gainPct"] == 0.0


def test_sip_rising_nav_averaging():
    # Month-end NAVs rising 100 -> 111: SIP gain must be positive but below
    # the 11% point-to-point rise, because early installments bought cheaper.
    import calendar
    from datetime import date

    nav = []
    d = date(2022, 1, 3)
    # Build daily series across 13 months with month-end NAVs 100..112.
    month_nav = {}
    y, m = 2022, 1
    for i in range(13):
        month_nav[(y, m)] = 100 + i
        m += 1
        if m > 12:
            m, y = 1, y + 1
    cur = d
    end = date(2023, 1, 31)
    while cur <= end:
        nav.append((cur, float(month_nav[(cur.year, cur.month)])))
        cur += timedelta(days=1)
    # Keep only business days to mimic NAV calendars.
    nav = [(dd, v) for dd, v in nav if dd.weekday() < 5]
    s = _sip(nav)
    assert s["1Y"]["invested"] == 120000
    assert s["1Y"]["value"] > 120000
    assert 0 < s["1Y"]["gainPct"] < 11


def test_base_name_dedupe():
    assert base_name("Parag Parikh Flexi Cap Fund - Direct Plan - Growth") == (
        base_name("Parag Parikh Flexi Cap Fund - Regular Plan - Growth")
    )
    assert base_name("SBI Liquid Fund - Regular Plan - Growth") == "SBI Liquid Fund"


def test_growth_plan_filter():
    assert _is_growth_plan("ABC Flexi Cap Fund - Direct Plan - Growth")
    assert not _is_growth_plan("ABC Flexi Cap Fund - Direct Plan - Monthly IDCW Payout")
    assert not _is_growth_plan("ABC Fund - Regular Plan - Dividend")


def test_category_matching():
    assert matches_category("Parag Parikh Flexi Cap Fund - Direct Plan - Growth", "flexi-cap")
    assert matches_category("HDFC ELSS Tax Saver Fund - Growth", "elss")
    assert matches_category("Nippon India Nifty 50 Index Fund - Growth", "index")
    assert not matches_category("SBI Liquid Fund - Growth", "flexi-cap")
    assert not matches_category("Anything", "nope")
