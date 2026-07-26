import os

# Cache TTLs (seconds)
QUOTE_TTL = int(os.getenv("QUOTE_TTL", "120"))
HISTORY_TTL = int(os.getenv("HISTORY_TTL", "3600"))
NEWS_TTL = int(os.getenv("NEWS_TTL", "900"))
ANALYSIS_TTL = int(os.getenv("ANALYSIS_TTL", "600"))

# Supabase (optional — falls back to SQLite when unset)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

SQLITE_PATH = os.getenv("SQLITE_PATH", os.path.join(os.path.dirname(__file__), "..", "trendwise.db"))

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# "auto": use live data, fall back to deterministic synthetic data when the
# provider is unreachable. "on": always synthetic. "off": live only.
DEMO_MODE = os.getenv("DEMO_MODE", "auto").lower()

DISCLAIMER = (
    "TrendWise is an educational analysis tool, not SEBI-registered investment advice. "
    "Markets carry risk; do your own research before trading."
)
