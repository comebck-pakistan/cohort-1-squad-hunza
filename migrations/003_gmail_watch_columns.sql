-- Additive only. INGEST-01 needs to remember, per connected mailbox:
--   - history_id: Gmail's cursor - "give me everything that changed since
--     this point" (via users.history.list). Without it we'd have no way to
--     know what's new when a push notification arrives.
--   - watch_expiration: Gmail push subscriptions (users.watch) expire after
--     a maximum of 7 days and must be renewed before then, or notifications
--     silently stop arriving.

ALTER TABLE public.gmail_connections
  ADD COLUMN IF NOT EXISTS history_id text,
  ADD COLUMN IF NOT EXISTS watch_expiration timestamptz;

CREATE INDEX IF NOT EXISTS idx_gmail_connections_address
  ON public.gmail_connections (gmail_address);
