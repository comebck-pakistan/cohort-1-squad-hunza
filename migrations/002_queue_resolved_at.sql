-- Additive only. Needed for QUEUE-02: a "needs attention" item has to be
-- explicitly dismissable (DELETE /queue/{email_id}) independent of whether
-- a reply was ever sent through this app - e.g. the recruiter handled it by
-- phone. resolved_at also gets set automatically when a draft is approved
-- and sent (see drafts/service.py::approve_and_send_draft), so most items
-- clear themselves without any manual action.

ALTER TABLE public.email_categories
  ADD COLUMN IF NOT EXISTS resolved_at timestamptz;

CREATE INDEX IF NOT EXISTS idx_email_categories_priority
  ON public.email_categories (priority);
