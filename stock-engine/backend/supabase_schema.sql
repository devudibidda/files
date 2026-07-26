-- TrendWise tables for Supabase (run in the SQL editor of your free project).
-- Then set SUPABASE_URL and SUPABASE_KEY (service_role or anon key) on the backend.

create table if not exists watchlist (
  client_id text not null,
  symbol text not null,
  added_at timestamptz default now(),
  primary key (client_id, symbol)
);

create table if not exists signal_history (
  symbol text not null,
  day date not null,
  score real not null,
  verdict text not null,
  price real,
  primary key (symbol, day)
);

-- The backend talks to PostgREST with the service key; keep RLS off for
-- these tables or add policies matching your needs.
