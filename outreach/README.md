# GTM Job Outreach System (n8n)

A full outreach engine for your GTM engineer job hunt. Every morning it:

1. **Scrapes** fresh remote GTM engineer jobs (LinkedIn US + UK) via your existing `scraper.py`
2. **Dedupes** against everyone you've already contacted (Google Sheet log)
3. **Enriches** each company: **Clearbit autocomplete** (free, no key) resolves the company name to its domain; **Hunter.io Domain Search** then returns the people on that domain with names, titles, and verified emails, and the pipeline picks the right decision maker (founder/CEO for startups, CRO/VP Sales for bigger companies)
4. **Researches** each company's GTM motion with **Claude** and writes a custom one-liner pitch + a personalized cold email
5. **Generates a tailored one-page resume PDF** for each specific role (from your `profile.md` — facts only, nothing invented)
6. **Reaches out** via Gmail with the resume attached (drafts by default; flip one switch for full auto-send)
7. **Logs** everything to a Google Sheet
8. A second workflow **follows up** automatically after 3 days (max 2 bumps), detects replies, and stops bumping anyone who answered

> ⚠️ Runs on **local/self-hosted n8n only** (it executes your local scraper, reads
> local files, and uses Chrome for PDF rendering). n8n Cloud won't work as-is.

---

## Files

```
outreach/
├── README.md                      ← you are here
├── profile.md                     ← FILL THIS IN FIRST (your resume source of truth)
├── resume_template.html           ← PDF styling (edit colors/fonts if you like)
└── workflows/
    ├── 1_gtm_outreach_pipeline.json   ← main daily pipeline
    └── 2_followup_engine.json         ← reply detection + follow-up bumps
```

## Setup (one time, ~30 min)

### 1. Fill in your profile
Open `profile.md` and replace every `[FILL IN]`. Be specific — numbers and
tool names directly improve every resume and email the system writes.

### 2. Install and start n8n
```bash
npm install -g n8n
n8n
```
Open http://localhost:5678 and create your local account.

### 3. Create the tracking Google Sheet
1. Create a new Google Sheet, rename the first tab to **Contacted**
2. Paste this into cell A1, then use **Data ▸ Split text to columns**:
   ```
   date,company,position,location,job_url,company_headcount,company_website,company_linkedin,contact_name,contact_title,contact_email,contact_linkedin,one_liner,gtm_insights,email_subject,status,thread_id,message_id,followups,last_touch
   ```
3. Copy the sheet's URL — you'll paste it into 4 nodes in step 6.

### 4. Get your API keys
- **Clearbit**: no key needed. Company-domain resolution uses Clearbit's free
  public autocomplete endpoint.
- **Hunter.io**: hunter.io → API → copy key. Domain Search returns the decision
  maker (name/title) **and** their verified email from the company domain. Free
  plan ≈ 25–50 lookups/month (1 per company).
- **Anthropic (Claude)**: console.anthropic.com → API Keys.
  ~10 companies/day costs only a few cents with Sonnet.

### 5. Create credentials in n8n (Credentials menu → Add)
| Credential type | Name it | Settings |
|---|---|---|
| Query Auth | `Hunter` | Name: `api_key`, Value: your Hunter key |
| Header Auth | `Anthropic` | Name: `x-api-key`, Value: your Anthropic key |
| Gmail OAuth2 | `Gmail` | Follow n8n's guided Google OAuth setup |
| Google Sheets OAuth2 | `Sheets` | Same Google Cloud project as Gmail |

⚠️ **Hunter is *Query* Auth**, not Header Auth — its key goes in the URL.

The Google OAuth setup is the fiddly one — n8n shows step-by-step instructions
inside the credential dialog (create a Google Cloud project, enable the Gmail +
Sheets APIs, add the redirect URL).

### 6. Import the workflows
1. n8n → Workflows → **Import from file** → pick `1_gtm_outreach_pipeline.json`, then `2_followup_engine.json`
2. In each workflow, open the nodes that show a ⚠️ and:
   - **Resolve Domain** node (Clearbit) → no credential needed (free public endpoint)
   - **Hunter: Domain Search** node → select the `Hunter` credential
   - **Claude nodes** → select the `Anthropic` credential
   - **Gmail nodes** → select the `Gmail` credential
   - **Google Sheets nodes** → select the `Sheets` credential AND paste your sheet URL into the Document field (or pick it from the dropdown list)

### 7. Test run (safe — drafts only)
The pipeline ships with `send_mode: 'draft'` in the **Config** node, so nothing
is emailed automatically. Click **Execute workflow** in workflow 1, then check:
- your Gmail **Drafts** folder — review the personalized emails + attached resumes
- your Google Sheet — one row per company

Tip for the first test: in the Config node set `run_scraper: false` (reuses
your latest Desktop export instead of scraping for 8 minutes) and in the
**Limit Per Run** node set Max Items to `2`.

### 8. Go live
When you're happy with the drafts:
- Config node → change `send_mode` to `'send'`
- Toggle both workflows **Active** (top right switch)

That's it. Workflow 1 runs every morning at 8:30, workflow 2 bumps non-responders
at 10:00.

---

## How the pieces work

| Stage | Tool | What it does |
|---|---|---|
| Scrape | `scraper.py` | 28 LinkedIn query/location combos → ~500 jobs |
| Select | n8n Code | Best GTM role per company, skips contacted companies, caps at 10/day |
| Job detail | HTTP | Fetches the full job description for the selected ~10 only |
| Resolve domain | Clearbit (free, keyless) | Company name → domain via autocomplete |
| Find person + email | Hunter Domain Search | People on the domain with name, title, and verified email |
| Pick decision maker | n8n Code | Ranks people by title (founder/CEO → CRO/VP Sales/Growth → …); accepts only Hunter confidence ≥ 70 |
| Size gate | LLM estimate | Skips companies estimated larger than `max_employees` (Config) |
| Research + copy | Claude | GTM-motion insights, custom one-liner, 120-word personalized email |
| Resume | Claude + Chrome | Tailored one-pager from your profile.md → styled HTML → PDF |
| Send | Gmail | Draft or auto-send; first touch links to your resume (no attachment), no n8n attribution footer |
| Track | Google Sheets | Full log: contact, email, pitch, status, thread id |
| Follow-up | Workflow 2 | After 3 days: checks thread for a reply; replies → status `replied`; silence → AI-written bump (max 2) |

## Dials you can turn

- **Volume**: `Limit Per Run` node (set to ~2/day to stay inside Hunter's free tier; keeps Gmail deliverability healthy too)
- **Email confidence bar**: `Pick Decision Maker` node — accepts Hunter confidence `>= 70`; raise it to be stricter, lower to get more (riskier) emails
- **Send mode**: Config node `send_mode: 'draft' | 'send'`
- **Model**: Config node `model` — `claude-sonnet-4-6` (default) or `claude-opus-4-8` for max quality
- **Follow-up timing**: workflow 2 Config — `followup_after_days: 3`, `max_followups: 2`
- **Decision-maker titles**: edit the `rank()` function in *Pick Decision Maker* (it scores founder/CEO → CRO/VP Sales → … by regex)
- **Resume link**: Config node `resume_url` — the link added to every first-touch email
- **Email voice**: edit the "Voice notes" section of `profile.md`, or the prompt in *Build Strategist Prompt*

## Notes & limits

- **Skipped companies** (no decision maker / no email found) are logged with a
  skip status and won't be retried. Delete the row from the sheet to retry one.
- **Draft mode rows** get status `drafted` — the follow-up engine only tracks
  `sent` rows, so emails you send manually from Drafts won't get auto-bumps.
- **Hunter credits**: each company = 1 Hunter Domain Search. Free tier ≈ 25–50/month, so
  keep `Limit Per Run` around 2/day. Clearbit's domain autocomplete is free and keyless,
  so domain resolution costs nothing.
- **Gmail limits**: consumer Gmail allows ~500 sends/day; we use ~25 max. Fine.
- If a LinkedIn job page blocks the description fetch, the email still works —
  Claude just leans on the company website + role title instead.
