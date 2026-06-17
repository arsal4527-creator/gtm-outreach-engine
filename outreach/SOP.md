# 📘 GTM Outreach System — Your Operating Manual (SOP)

**Read this top to bottom once. Then keep it open and follow it like a checklist.**
No prior knowledge assumed. Every step tells you exactly what to click and what
you should see when it worked.

---

## 🧠 First, what is this thing? (2-minute read)

You're job-hunting for remote GTM engineer roles. Doing this by hand means:
find a job → figure out the company → find the founder → find their email →
research the company → write a custom email → tailor your resume → send → remember
to follow up. That's ~30 minutes **per company**.

This system does all of that automatically. You press one button (or let it run
every morning) and it produces ready-to-send emails — each one personalized, with
a resume tailored to that exact job, addressed to the right decision maker, with
their real email address.

It's built from 3 building blocks:

| Block | What it is | Think of it as… |
|---|---|---|
| **The Scraper** | A script that collects GTM jobs from LinkedIn | Your research intern |
| **n8n** | Free software that connects steps together | The assembly line / robot |
| **Google Sheet** | A spreadsheet that records everything | Your memory / tracker |

Plus a few services the assembly line phones for help:
- **Clearbit + Hunter** — Clearbit finds the company's domain (free, no key), then
  Hunter finds the decision maker and their verified email
- **Claude (AI)** — writes the emails and resumes
- **Gmail** — sends from your account

You don't need to understand *how* they work. You just need to plug them in once.
This document is that plug-in process.

---

## ⏱️ How long will this take?

- **One-time setup: ~45 minutes.** You do this once. Most of it is creating
  free accounts and clicking "Allow."
- **Daily use: 0 minutes** once it's live (runs by itself), or ~5 minutes if you
  want to review drafts before they send.

> 💡 **You do NOT need to know how to code.** You'll copy-paste a few things and
> click a lot of buttons. That's it.

---

# PART 1 — ONE-TIME SETUP

Do these in order. Don't skip. Check the box when each is done.

## ☐ Step 1 — Fill in your profile (15 min) — **THE MOST IMPORTANT STEP**

The AI builds every resume and email **only** from facts you give it. If this
file is empty, your emails will be empty. If it's detailed, they'll be great.

1. Open this file in any text editor (even TextEdit):
   `/Users/app/gtm-job-scraper/outreach/profile.md`
2. Replace **every** `[FILL IN]` with your real info — name, experience, skills,
   numbers ("booked 25 meetings/month", "cut response time 40%").
3. Save the file.

> ✅ **Done when:** there are no more `[FILL IN]` placeholders left in the file.
>
> 🆘 **Don't want to do it alone?** Paste your old resume or LinkedIn text to
> Claude in this chat and say "fill in my profile.md" — it'll do it for you.

---

## ☐ Step 2 — Install n8n, the robot (10 min)

n8n is the free app that runs the whole assembly line.

1. Open the **Terminal** app (press `Cmd + Space`, type "Terminal", hit Enter).
2. Copy-paste this line and press Enter:
   ```
   npm install -g n8n
   ```
   *(If it says "command not found: npm", you first need Node.js — go to
   https://nodejs.org, download the big green "LTS" button, install it, then
   come back and run the line above again.)*
3. Wait for it to finish (a few minutes — lots of text scrolling is normal).
4. Now start n8n by pasting this and pressing Enter:
   ```
   n8n
   ```
5. Leave that Terminal window **open** (closing it turns the robot off).
6. Open your web browser and go to: **http://localhost:5678**
7. Create a username and password when it asks (this is just for you, locally).

> ✅ **Done when:** you see the n8n welcome screen in your browser.

---

## ☐ Step 3 — Create your tracking spreadsheet (5 min)

This is your "memory" — it stops the system from emailing the same company twice
and records every email sent.

1. Go to https://sheets.new (makes a fresh Google Sheet).
2. At the bottom, double-click the tab named "Sheet1" and rename it to:
   **Contacted** (exact spelling, capital C).
3. Click cell **A1**. Copy the entire line below and paste it into A1:
   ```
   date,company,position,location,job_url,company_headcount,company_website,company_linkedin,contact_name,contact_title,contact_email,contact_linkedin,one_liner,gtm_insights,email_subject,status,thread_id,message_id,followups,last_touch
   ```
4. With A1 still selected, go to the menu: **Data ▸ Split text to columns**.
   The line will spread across the top row as proper column headers.
5. Look at your browser's address bar and **copy the whole URL** of this sheet.
   Paste it somewhere safe (a notes app) — you'll need it in Step 6.

> ✅ **Done when:** row 1 has 20 column headers, each in its own cell.

---

## ☐ Step 4 — Get your two API keys (10 min)

An "API key" is just a password that lets the robot use a service on your behalf.
You need **two** keys (Hunter and Claude). Company-domain lookup uses Clearbit's
free public endpoint, which needs **no key at all**.

### Hunter.io key (finds the decision maker + their email)
Hunter looks at a company's domain and returns the people there with their names,
titles, and verified emails. That's both *who* to contact and *how*.
1. Go to https://hunter.io and sign up (free).
2. Click your avatar ▸ **API** (or go to hunter.io/api-keys).
3. Copy your **API key**, label it "HUNTER KEY" in your notes.
   - Free plan = ~25–50 lookups/month. To stay free, keep your daily cap low
     (see Step 9). Upgrade later if you want more volume.

### Anthropic / Claude key (writes the emails + resumes)
1. Go to https://console.anthropic.com and sign up / log in.
2. Left menu ▸ **API Keys** ▸ **Create Key**.
3. Copy the key (starts with `sk-ant-`), label it "CLAUDE KEY" in your notes.
4. You'll need a few dollars of credit on the account — **Billing ▸ Add credits**.
   $5 lasts a very long time (≈10 companies/day costs pennies).

> ✅ **Done when:** you have two keys saved in your notes: HUNTER KEY and CLAUDE KEY.
> (No Apollo key, no Clearbit key — domain lookup is free and keyless.)

---

## ☐ Step 5 — Connect the 4 accounts to n8n (10 min)

In n8n, "credentials" are where you store those keys and log into Google. You set
each up **once**.

In n8n, click **Credentials** in the left sidebar, then **Add credential** for each.
(There's no Apollo or Clearbit credential — Clearbit's domain lookup is keyless.)

### 5a. Hunter
- Add credential ▸ pick **"Query Auth"** (⚠️ *Query* Auth, not Header Auth — Hunter's
  key rides in the URL).
- **Name** field: type `Hunter`
- **Name** (the query parameter name): type `api_key`
- **Value**: paste your HUNTER KEY
- Save.

### 5b. Claude
- Add credential ▸ **"Header Auth"**.
- **Name** field: type `Anthropic`
- **Name** (header name): type `x-api-key`
- **Value**: paste your CLAUDE KEY
- Save.

### 5c. Gmail — ⭐ this is how emails send from YOUR account
- Add credential ▸ search **"Gmail OAuth2"**.
- n8n shows on-screen instructions to create a Google "OAuth" app. It looks
  like a lot, but it's just clicking through Google's setup. Follow n8n's steps:
  you'll create a free Google Cloud project, turn on the **Gmail API**, and copy
  two values (Client ID + Client Secret) back into n8n.
- Then click **"Sign in with Google"** in n8n → choose your Gmail → click
  **Allow**. ✅ That handshake is what lets n8n send as you.

### 5d. Google Sheets
- Add credential ▸ **"Google Sheets OAuth2"**.
- Use the **same** Google Cloud project you just made (turn on the **Sheets API**
  in it too). Sign in, Allow.

> 😅 **Step 5c/5d is the hardest part of the whole setup.** Google's OAuth screens
> are fiddly. Go slowly, follow n8n's built-in instructions exactly. If you get
> stuck, screenshot the screen and ask Claude in this chat — describe what you see.
>
> ✅ **Done when:** Credentials list shows 4 entries: Hunter, Anthropic,
> Gmail, Google Sheets, each with a green check.

---

## ☐ Step 6 — Load the two workflows (5 min)

The "workflows" are the assembly lines I already built. You just import them.

1. In n8n: top-left ▸ **Workflows** ▸ the **"⋯"** or **Import** button ▸
   **Import from File**.
2. Choose this file:
   `/Users/app/gtm-job-scraper/outreach/workflows/1_gtm_outreach_pipeline.json`
3. Import again and choose:
   `/Users/app/gtm-job-scraper/outreach/workflows/2_followup_engine.json`

Now connect your credentials and sheet to each workflow. Open workflow 1. Some
boxes (called "nodes") have a small ⚠️ warning — that just means "pick a
credential here." For each:
- The box named **Resolve Domain** (Clearbit) → no credential needed, leave it alone.
- The box named **Hunter: Domain Search** → pick **Hunter**.
- Boxes named **Claude: …** → pick **Anthropic**.
- Boxes named **Gmail: …** → pick **Gmail**.
- Boxes named **…Log** / **Get Contacted** / **Append** (Google Sheets) → pick
  **Google Sheets**, AND in the "Document" field paste your **sheet URL** from
  Step 3 (or pick it from the dropdown). Set Sheet to **Contacted**.

Do the same in workflow 2 (it has Claude, Gmail, and Google Sheets boxes).

> ✅ **Done when:** no boxes show a red ⚠️ about missing credentials.

---

# PART 2 — DAILY USE

## ☐ Step 7 — Your first test run (safe — nothing sends) (5 min)

The system starts in **DRAFT MODE**. It writes emails into your Gmail Drafts so
you can read them. It does **not** send anything until you say so. Let's test small.

1. Open **workflow 1** in n8n.
2. Click the box named **Config**. Find these two lines and set them for a quick test:
   - `run_scraper: false`  ← reuses your existing job list instead of scraping 8 min
   - (leave `send_mode: 'draft'`)
3. Click the box named **Limit Per Run**. Change "Max Items" to **2** (just 2
   companies for the test).
4. Top-right: click **▶ Execute workflow**.
5. Watch the boxes light up green one by one (takes 1–2 min for 2 companies).

Now check the results:
- Open **Gmail ▸ Drafts** — you should see up to 2 new draft emails, each a
  personalized message with a **link to your resume** (and a link to the project
  repo + demo). No file is attached on the first email — that keeps it out of spam.
- Open your **Google Sheet** — you should see up to 2 new rows.

> ✅ **Done when:** you see real drafts in Gmail with the resume + repo links in them.
>
> 🆘 If a box turns **red**, click it to read the error, then paste that error to
> Claude in this chat. (Common ones: wrong credential picked, or Claude account
> needs credits.)

---

## ☐ Step 8 — Read the drafts, fix the voice (5 min)

Open one of the draft emails. Ask yourself:
- Does it sound like me? → if not, edit the "Voice notes" section in `profile.md`.
- Is the resume accurate? → if it's thin, add more detail to `profile.md`.
- Is it emailing the right person? → adjust the title ranking in the **Pick Decision
  Maker** box if needed (see README).

Re-run Step 7 until you love the output. **This is the tuning phase — worth doing.**

---

## ☐ Step 9 — Go live (2 min)

When the drafts look great:

1. Open workflow 1 ▸ **Config** box ▸ change `send_mode` to `'send'`.
   (Also set `run_scraper: true` again so it pulls fresh jobs.)
2. Set **Limit Per Run** to your comfort level. ⚠️ **Each company = 1 Hunter lookup.**
   On Hunter's free plan (~25–50/month) set this to **2** so you don't run dry
   (≈50/month). Upgrade Hunter, or switch email source later, to go higher.
3. Top-right of **both** workflows: flip the **Active** switch to ON.

That's it. From now on:
- **8:30 AM daily** — workflow 1 finds new jobs and emails 10 decision makers.
- **10:00 AM daily** — workflow 2 checks for replies and nudges non-responders
  (max 2 nudges, and it stops the moment someone replies).

> ⚠️ Keep the Terminal window from Step 2 open, or run n8n on an always-on machine,
> for the daily schedule to fire. If your Mac sleeps, it runs next time it's awake.

---

# PART 3 — TRACKING IT

You have **two** ways to see what's happening:

### Option A — The Google Sheet (always up to date, zero setup)
It fills in automatically. Every row = one company. The **status** column tells you:
| status | meaning |
|---|---|
| `drafted` | email written, sitting in your Drafts (draft mode) |
| `sent` | email sent from your Gmail |
| `replied` | 🎉 they wrote back — go check your inbox! |
| `email_not_found` / `email_low_confidence` / `no_decision_maker_found` | Hunter couldn't find a confident email, or no decision maker — skipped |

### Option B — The visual Dashboard (pretty charts)
I built you a dashboard file: `outreach/dashboard.html`.
1. In your Google Sheet: **File ▸ Download ▸ Comma-separated values (.csv)**.
2. Double-click `dashboard.html` to open it in your browser.
3. Click **"Load CSV"** and pick the file you just downloaded.
4. See your totals, reply rate, funnel, and a searchable table of every contact.

Re-download + reload whenever you want a fresh view. (Setup instructions for a
live auto-updating version are inside the dashboard itself.)

> 🌐 **Want a public demo?** A ready-made anonymized dataset lives at
> `outreach/sample_outreach.csv`. To publish the dashboard as a live page a founder
> can click (the proof-of-work move): make the repo public, enable **GitHub Pages**
> on the repo (Settings ▸ Pages ▸ deploy from `main`), and the dashboard loads
> `sample_outreach.csv` so visitors see it running without any of your real contacts.
> Put that Pages URL in `repo_url`/`resume_url` context and link it from the email.

---

# 🆘 TROUBLESHOOTING CHEAT SHEET

| Problem | Fix |
|---|---|
| `command not found: npm` | Install Node.js from https://nodejs.org, then retry |
| n8n page won't load | Is the Terminal running `n8n`? It must stay open |
| A box turns red | Click it, read the error, paste it to Claude here |
| "credential not selected" | Open that box, pick the matching credential from dropdown |
| No drafts appeared | Check the Gmail box uses the Gmail credential; check status column in sheet for skip reasons |
| Claude box errors about credits | Add $5 at console.anthropic.com ▸ Billing |
| Emails go to wrong person | Edit the title ranking in **Pick Decision Maker** box |
| It emailed someone twice | Shouldn't happen — the sheet prevents it. Don't delete sheet rows |
| Want fewer/more per day | **Limit Per Run** box → change Max Items |

---

# 📋 QUICK REFERENCE — the only dials you'll touch

All in workflow 1's **Config** box (and workflow 2's **Config (Follow-ups)** box):

| Setting | Where | What it does |
|---|---|---|
| `send_mode` | Config | `'draft'` = review first, `'send'` = auto |
| `run_scraper` | Config | `true` = find fresh jobs, `false` = reuse last list |
| `model` | Config | `claude-sonnet-4-6` (cheap/fast) or `claude-opus-4-8` (best) |
| Max Items | Limit Per Run box | how many companies per day |
| `followup_after_days` | Config (Follow-ups) | days to wait before a nudge |
| `max_followups` | Config (Follow-ups) | how many nudges before giving up |

**You're done. Start with Step 1.** 🚀
