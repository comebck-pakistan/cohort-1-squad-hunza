-- Additive only. No existing tables are modified except email_categories,
-- which only gets new nullable columns.

-- Needed because JWT refresh tokens must be revocable (logout, reuse-detection,
-- "log out of all devices"), which requires server-side state - a pure stateless
-- JWT refresh token can't be revoked before it expires.
CREATE TABLE public.refresh_tokens (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  token_hash text NOT NULL UNIQUE,        -- SHA-256 hex of the raw refresh token; raw value is never stored
  issued_at timestamp with time zone DEFAULT now(),
  expires_at timestamp with time zone NOT NULL,
  revoked_at timestamp with time zone,
  replaced_by uuid,                       -- points to the token that replaced this one on rotation
  user_agent text,
  ip_address text,
  CONSTRAINT refresh_tokens_pkey PRIMARY KEY (id),
  CONSTRAINT refresh_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE
);

CREATE INDEX idx_refresh_tokens_user_id ON public.refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token_hash ON public.refresh_tokens(token_hash);

-- Feature 3 (Priority Detection) - additive columns on the existing classification
-- output table, rather than a new table, since priority is produced by the same
-- Grok call as category.
ALTER TABLE public.email_categories
  ADD COLUMN IF NOT EXISTS priority text,                 -- 'high' | 'medium' | 'low'
  ADD COLUMN IF NOT EXISTS priority_reason text;           -- short justification, optional, for recruiter UI tooltip
