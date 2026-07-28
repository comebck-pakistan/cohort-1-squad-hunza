"""
End-to-end integration test against a REAL Gmail inbox. Not a mocked unit
test - this actually calls Google's APIs and your live Grok/Groq key, so it
costs real API calls and requires state already set up by hand first.

Prerequisites (do these once, manually, via Swagger before running this):
  1. Log in: GET /auth/google/login in a browser, get an access_token.
  2. Connect a mailbox: GET /gmail/connect -> approve on Google's consent
     screen (make sure the Gmail permission checkboxes are ticked).
  3. Send yourself (or a test account) at least one email that looks like a
     real candidate email, e.g. subject "Application for Backend Role",
     asking a question, so classification/priority/draft have something
     meaningful to work with.
  4. Fill in TEST_ACCESS_TOKEN and TEST_CONNECTION_ID below, or set them as
     env vars (E2E_ACCESS_TOKEN, E2E_CONNECTION_ID) - env vars take priority.

Run with:  python -m pytest test/test_gmail_e2e.py -v -s
(-s so you can see the print statements walking through each stage)

This is deliberately NOT wired into normal `pytest` CI runs implicitly -
it's skipped automatically if the required credentials aren't provided,
so it won't break automated test runs for teammates who haven't set this up.
"""
import os

import httpx
import pytest

BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8000")
ACCESS_TOKEN = os.getenv("E2E_ACCESS_TOKEN", "")       # paste a fresh access_token here for local runs
CONNECTION_ID = os.getenv("E2E_CONNECTION_ID", "")     # paste your gmail_connections.id here

requires_live_gmail = pytest.mark.skipif(
    not ACCESS_TOKEN or not CONNECTION_ID,
    reason="Set E2E_ACCESS_TOKEN and E2E_CONNECTION_ID (env vars or in this file) to run the live Gmail E2E test.",
)


def _headers():
    return {"Authorization": f"Bearer {ACCESS_TOKEN}"}


@requires_live_gmail
def test_full_pipeline_against_real_inbox():
    with httpx.Client(base_url=BASE_URL, timeout=60) as client:

        # 1. Sync real Gmail messages - this also auto-runs the AI pipeline
        #    inline (classify -> duplicate-check -> draft -> embed) for every
        #    newly-inserted email, per gmail_integration/service.py::sync_now.
        print("\n[1/6] Syncing Gmail...")
        resp = client.post(f"/gmail/{CONNECTION_ID}/sync", headers=_headers())
        assert resp.status_code == 200, resp.text
        sync_result = resp.json()
        print(f"    checked={sync_result['checked']} inserted={sync_result['inserted']} skipped={sync_result['skipped_existing']}")
        assert sync_result["checked"] > 0, "No messages found - is there mail in the connected inbox?"

        # 2. List emails, confirm at least one has been classified
        print("[2/6] Fetching emails...")
        resp = client.get("/emails", headers=_headers())
        assert resp.status_code == 200, resp.text
        emails = resp.json()
        assert len(emails) > 0, "No emails found after sync"
        target_email = emails[0]
        print(f"    using email_id={target_email['id']} subject={target_email.get('subject')!r}")

        # 3. Needs-attention queue should be a valid (possibly empty) list -
        #    only high-priority unresolved items appear here.
        print("[3/6] Checking needs-attention queue...")
        resp = client.get("/queue", headers=_headers())
        assert resp.status_code == 200, resp.text
        print(f"    {len(resp.json())} item(s) currently need attention")

        # 4. A draft should already exist for the synced email (auto-generated
        #    during sync). Fetch it.
        print("[4/6] Fetching auto-generated draft...")
        resp = client.get(f"/drafts/by-email/{target_email['id']}", headers=_headers())
        assert resp.status_code == 200, f"No draft found for email {target_email['id']}: {resp.text}"
        draft = resp.json()
        draft_id = draft["id"]
        print(f"    draft_id={draft_id} status={draft['status']}")
        print(f"    preview: {draft['draft_body'][:100]}...")

        # 5. DRAFT-04 - edit the draft, confirm the correction was logged
        #    (indirectly - PATCH succeeding and returning status='edited' is
        #    the observable proof; draft_corrections itself is checked via
        #    Supabase directly if you want to confirm the row was written).
        print("[5/6] Editing draft (DRAFT-04 correction logging)...")
        edited_body = draft["draft_body"] + "\n\n(edited by E2E test)"
        resp = client.patch(f"/drafts/{draft_id}", headers=_headers(), json={"draft_body": edited_body})
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "edited"
        print("    edit saved, status=edited")

        # 6. DRAFT-03 - approve and actually send. THIS SENDS A REAL EMAIL.
        #    Only run this against a test inbox/test candidate address you
        #    control, never against a real candidate's email by accident.
        if os.getenv("E2E_CONFIRM_SEND") != "yes":
            pytest.skip(
                "Skipping the real-send step. Set E2E_CONFIRM_SEND=yes to actually "
                "send an email during this test (only do this against a test inbox)."
            )

        print("[6/6] Approving and sending draft (DRAFT-03)...")
        resp = client.post(f"/drafts/{draft_id}/approve", headers=_headers())
        assert resp.status_code == 200, resp.text
        sent_draft = resp.json()
        assert sent_draft["status"] == "sent"
        assert sent_draft["sent_at"] is not None
        print(f"    sent! gmail_draft_id={sent_draft.get('gmail_draft_id')}")

        # Confirm QUEUE-02 auto-resolved this email after sending
        resp = client.get("/queue", headers=_headers())
        queue_ids = [item["id"] for item in resp.json()]
        assert target_email["id"] not in queue_ids, "Email should have auto-resolved out of the queue after sending"
        print("    confirmed: email auto-resolved out of needs-attention queue")

        print("\nFull pipeline verified end-to-end against a real inbox.")
