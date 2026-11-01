import os

# Cache TTLs (seconds)
QUOTE_TTL = int(os.getenv("QUOTE_TTL", "120"))
HISTORY_TTL = int(os.getenv("HISTORY_TTL", "3600"))
NEWS_TTL = int(os.getenv("NEWS_TTL", "900"))
ANALYSIS_TTL = int(os.getenv("ANALYSIS_TTL", "600"))

# Upstox (optional, Yahoo is the fallback when unset). The Analytics
# Token is a 1-year read-only token from the Developer Apps page; on
# Render it is set in the dashboard, never committed to the repo.
UPSTOX_ANALYTICS_TOKEN = os.getenv("UPSTOX_ANALYTICS_TOKEN", "")

# Supabase (optional, falls back to SQLite when unset)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

SQLITE_PATH = os.getenv("SQLITE_PATH", os.path.join(os.path.dirname(__file__), "..", "trendwise.db"))

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

DISCLAIMER = (
    "TrendWise is an educational analysis tool, not SEBI-registered investment advice. "
    "Markets carry risk; do your own research before trading."
)
