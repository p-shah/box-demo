# Secure Client Reporting Portal — Box AI demo

A custom wealth-management client portal built on Box, modeled on the
[Morgan Stanley Wealth Management / Box story](https://blog.box.com/morgan-stanley-wealth-management-transforms-its-digital-client-experience-box).
Advisors upload quarterly statements, Box classifies and secures them, and
Box AI turns each statement into an advisor briefing and a structured
financial-highlights dashboard — all inside a custom React front end instead
of the Box web app.

## What it demonstrates

- **Automated classification** — uploads apply a metadata template
  (`clientReportInfo`), the trigger a real Shield policy would key off of.
- **Box AI, beyond a chatbot** — a single-item `ai/ask` call produces an
  advisor briefing (bulleted, cited), and `ai/extract_structured` pulls
  account values, net gain, and the largest holding straight out of the PDF
  into a stat-tile dashboard.
- **Governed sharing** — view-only, download-disabled, auto-expiring shared
  links, created on demand.
- **An audit trail** — a live activity feed standing in for the admin
  console / Events API story.

## Architecture

```
frontend/   React (Vite) — custom UI, talks only to the Flask API
backend/    Flask API — wraps box-sdk-gen (auth, folders, upload,
            metadata, Box AI ask/extract, shared links)
```

The frontend never talks to Box directly; the backend authenticates via
Client Credentials Grant (CCG) and does all Box API calls.

## Setup

### 1. Box

- A **Custom App** in the [Box developer console](https://app.box.com/developers/console)
  with auth method **"Server Authentication (Client Credentials Grant)"**,
  authorized by an enterprise admin (Admin Console → Apps → Custom Apps
  Manager). Note its Client ID and Client Secret.
- If acting as your own account (`BOX_USER_ID`, the simpler path — no
  re-sharing needed), the app also needs the **"Generate User Access
  Tokens"** scope approved by an admin. If acting as the enterprise Service
  Account instead (`BOX_ENTERPRISE_ID`), that account starts with no folder
  access — collaborate it into the portal root folder first.
- A metadata template `clientReportInfo` (scope `enterprise`) must exist —
  run `python setup_metadata.py` once if it hasn't already been created.
  This one-off script still uses a plain developer token (`BOX_DEVELOPER_TOKEN`)
  since it's a single manual run, not the running app.
- A portal root folder in Box holding one subfolder per client. Note its
  folder ID.

### 2. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # or reuse the repo's .venv
pip install -r requirements.txt
cp .env.example .env   # fill in BOX_CLIENT_ID, BOX_CLIENT_SECRET, BOX_USER_ID
                        # (or BOX_ENTERPRISE_ID), and BOX_PORTAL_ROOT_FOLDER_ID
python app.py           # http://localhost:5001 — auto-loads .env via python-dotenv
```

Unlike a developer token, CCG credentials don't expire every 60 minutes —
the SDK refreshes the access token automatically, so the backend process
can stay up across a whole demo session without re-pasting anything.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev              # http://localhost:5173, proxies /api to :5001
```

Open `http://localhost:5173` — that's the whole demo surface, no Box UI
involved.

## Security note

Both root-level scripts previously had a live Box developer token hardcoded
as a string literal (already committed in git history via `setup_metadata.py`
in the initial commit). Both now read `BOX_DEVELOPER_TOKEN` from the
environment instead. The old token is short-lived and has since been
superseded, but since it's in git history, treat any token that's ever been
hardcoded as burned — regenerate rather than reuse it. If you want it
scrubbed from history entirely (`git filter-repo` / BFG), say so before I
touch history — it rewrites commit hashes and needs a force-push.
