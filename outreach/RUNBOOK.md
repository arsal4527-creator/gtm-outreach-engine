# 🚀 GTM Outreach — Operating Runbook

**The optimized, step-by-step way to run the system.** This reflects the *current*
state (all fixes applied). If you only read one doc, read this one.

---

## ⚡ TL;DR — the daily run (5 steps)

1. **Start n8n via the launcher** (never plain `n8n`):
   `zsh /Users/app/gtm-job-scraper/start-n8n.command`
2. Open **http://localhost:5678**
3. Open **workflow 1** → check **Config** (settings below) → **Execute**
4. Review **Gmail → Drafts** (or let it send if you're live)
5. Open **`outreach/dashboard.html`** → Load your sheet CSV → read the numbers

That's it. Everything below is detail + troubleshooting.

---

## 1. Starting n8n — ALWAYS use the launcher

```
zsh /Users/app/gtm-job-scraper/start-n8n.command
```
(or double-click `start-n8n.command` in Finder)

**Why this matters:** the launcher sets three things n8n needs, and starting any
other way is what caused most of the errors you hit:
| Setting | Fixes |
|---|---|
| `NODE_OPTIONS=--dns-result-order=ipv4first` | the Google Sheets `ETIMEDOUT` (your network's IPv6 to Google is broken — this forces IPv4) |
| `NODES_EXCLUDE="[]"` | "Unrecognized node type: executeCommand" |
| `N8N_RESTRICT_FILE_ACCESS_TO=...` | "Access to the file is not allowed" |

**Rule: if you ever see a connection timeout, you started n8n the wrong way. Ctrl+C and relaunch with the command above.**

To stop n8n: `Ctrl + C` in its terminal. Leave the window open while using it.

---

## 2. Config settings (workflow 1 → "Config" node)

| Setting | Recommended | What it does |
|---|---|---|
| `send_mode` | `'draft'` → `'send'` | draft = review in Gmail first; send = auto-send. **Start draft.** |
| `run_scraper` | `false` for testing, `true` for fresh jobs | `false` = instantly reuse last export (no wait). `true` = scrape fresh (~6–8 min). |
| `max_employees` | `400` | skips companies bigger than this (AI estimate). Raise for more volume, lower to stay tiny-startup. |
| `model` | `claude-sonnet-4-6` | email/resume quality. Sonnet ≈ $0.08/company. Swap to `claude-haiku-4-5-20251001` to cut cost ~3×. |

**Limit Per Run node** (separate node): `Max Items` = **40** per run. Raise to run more at once (cost + time scale up).

---

## 3. The optimized run sequence

**First, get ONE clean batch (draft mode):**
1. Launcher → n8n up → reload localhost:5678
2. Workflow 1 → **Config**: `send_mode: 'draft'`, `run_scraper: false` *(skip the scrape — reuse the existing 106-company export; instant)*
3. **Execute**
4. Watch nodes go green. With 40 companies it takes a few minutes.
5. Check **Gmail → Drafts**: each should have a personalized email + attached tailored resume + your Calendly link.

**Then, once the drafts look good:**
6. **Config** → `send_mode: 'send'`
7. **Re-run** — now it actually sends (only NEW companies; the sheet skips anyone already done).
8. To pull fresh jobs going forward: `run_scraper: true` (adds ~6–8 min/run).

**For hands-off daily operation:**
9. Toggle workflow 1 **Active** (top-right) → runs daily at 8:30am
10. Import + activate **workflow 2** (follow-ups) → bumps non-responders at 10am, stops when they reply
11. Keep your Mac awake around those times (it's local).

---

## 4. The golden rules (what NOT to do)

- ❌ **Don't clear the Google Sheet.** It's your dedup ledger — it's what stops re-emailing the same company and remembers who's done. Clearing it breaks the "already contacted" memory.
- ❌ **Don't keep duplicate workflows.** After re-importing, delete old copies so only ONE workflow 1 exists.
- ❌ **Don't start n8n with plain `n8n` in an old terminal** — use the launcher.
- ✅ **Re-import workflow 1** after any change to the workflow file (delete old → import).
- ✅ The **scraper (`scraper.py`) changes apply automatically** — no re-import needed for those.

---

## 5. Reading the dashboard

Open **`/Users/app/gtm-job-scraper/outreach/dashboard.html`** (double-click in Finder).
Then: Google Sheet → **File ▸ Download ▸ CSV** → click **Load CSV** in the dashboard.

What to watch:
- **Reply Rate** — the metric that matters. Aim to improve it by tuning the email.
- **First Sends / Total Sent** — volume out of your inbox (watch Gmail's ~500/day cap).
- **No-Email %** — companies Hunter couldn't find a contact for (expect 25–40%; mostly tiny startups).
- **"What to tune"** panel — auto-advice based on your numbers.
- **Booked calls** — track in **Calendly's own dashboard** (the real success metric).

---

## 6. Cost management

- **Sonnet ≈ $0.08/company.** Your **$5 ≈ ~60 companies.**
- When the credit runs out, the run **pauses** (no harm) — add credit at console.anthropic.com → Billing, and it resumes (the sheet remembers who's done).
- To run your whole list uninterrupted, top up **~$10**.
- To stretch the budget ~3×: set `model: 'claude-haiku-4-5-20251001'` in Config (slightly less polished, much cheaper).

---

## 7. Troubleshooting — every error → exact fix

| Error / symptom | Fix |
|---|---|
| `connect ETIMEDOUT 2001:...` (IPv6) on a Google Sheets node | You started n8n without the IPv4 fix. **Ctrl+C → relaunch via `start-n8n.command`.** |
| `Unrecognized node type: n8n-nodes-base.executeCommand` | Same — relaunch via the launcher (sets `NODES_EXCLUDE`). |
| `Access to the file is not allowed. Allowed paths: ~/.n8n-files` | Same — relaunch via the launcher (sets file access). |
| `Sheet with name Contacted not found` | The sheet tab must be named **exactly** `Contacted` (capital C, no spaces). |
| `404 / you can only access workflows owned by you` (in terminal) | Harmless — a stale browser tab pointing at a deleted workflow. Close it, open the Workflows list fresh. Also delete duplicate workflows. |
| `community-nodes / Strapi timeout` in terminal | Harmless background noise (n8n fetching its node catalog). The IPv4 launcher fixes it too. |
| Scraper "running for 20+ minutes" | Set `run_scraper: false` (reuse export, instant) for testing. Fresh scrape is now ~6–8 min. |
| Lots of `no_emails_found` | Mostly tiny startups Hunter has no data on — expected. Confidence cutoff is already lowered to 50. Bigger companies (raise `max_employees`) have better coverage. |
| `no_confident_contact` | Hunter found people but below the confidence bar — already loosened to 50 in "Pick Decision Maker". |
| Claude credit / 400 error | Out of Anthropic credit → top up at console.anthropic.com. |
| A box still times out after relaunch | Tell Claude — fallback is to move the dedup/log to a local file (zero Google dependency). |

---

## 8. What to expect (set realistic targets)

- **Email hit-rate: ~60–75%** of companies will yield a contact + email. The rest are too small for Hunter — that's normal, not a bug. They just get skipped.
- **Reply rate: ~2–5%** on good cold email. So ~40 sends → ~1–2 replies → conversations.
- **Goal math:** to land interviews this week, push **volume** (40+/day, send mode, follow-ups on) and watch reply rate in the dashboard. Closing a *signed* job in days is unlikely; landing *calls/interviews* is very doable.

---

## 9. Pending / optional upgrades

- **RevOps-agency source** (in progress) — find RevOps/outbound/GTM agencies via Serper, reach out with "you run RevOps for clients; I'm the GTM engineer who can deliver it." Better email coverage than tiny startups + a perfect fit for you. *(Needs your Serper API key.)*
- **Adzuna** — already coded in `scraper.py`; add a free key (developer.adzuna.com) to pull Indeed + hundreds of boards reliably (instead of scraping them directly, which is blocked).
- **Bounce tracking** — you said you'd handle this; add a `bounced` status + dashboard tile.

---

## Quick reference — file locations

```
Launcher:        /Users/app/gtm-job-scraper/start-n8n.command
Scraper:         /Users/app/gtm-job-scraper/scraper.py
Your profile:    /Users/app/gtm-job-scraper/outreach/profile.md   (resume + email source of truth)
Dashboard:       /Users/app/gtm-job-scraper/outreach/dashboard.html
Workflows:       /Users/app/gtm-job-scraper/outreach/workflows/1_gtm_outreach_pipeline.json
                 /Users/app/gtm-job-scraper/outreach/workflows/2_followup_engine.json
Job exports:     ~/Desktop/GTM_Jobs/gtm_jobs_*.json
Tracking sheet:  your "Contacted" Google Sheet (URL is wired into the workflow's Sheets nodes)
Public repo:     https://github.com/arsal4527-creator/gtm-outreach-engine
```
