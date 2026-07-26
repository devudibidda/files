"""Background refresh jobs: pre-warm the caches so requests stay fast."""
import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler

log = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _warm_market():
    from .market import market_overview
    try:
        market_overview()
        log.info("market overview cache warmed")
    except Exception as exc:
        log.warning("market warm failed: %s", exc)


def _warm_screener():
    from .screener import scan_universe
    try:
        scan_universe()
        log.info("screener cache warmed")
    except Exception as exc:
        log.warning("screener warm failed: %s", exc)


def _warm_news():
    from .news.rss import market_news
    try:
        market_news()
    except Exception as exc:
        log.warning("news warm failed: %s", exc)


def start():
    global _scheduler
    if os.getenv("SCHEDULER", "on").lower() == "off" or _scheduler:
        return
    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(_warm_market, "interval", minutes=5, next_run_time=None)
    _scheduler.add_job(_warm_screener, "interval", minutes=15)
    _scheduler.add_job(_warm_news, "interval", minutes=10)
    _scheduler.start()
    log.info("background scheduler started")


def stop():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
