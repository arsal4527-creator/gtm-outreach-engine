# GTM Outreach Engine

An end-to-end, AI-powered outbound system that turns "companies are hiring GTM
engineers" into personalized, ready-to-send applications — built to demonstrate
the exact GTM-engineering motion it automates.

It scrapes remote GTM-engineer roles, finds the right decision-maker and their
verified email, researches each company's go-to-market from the job description,
writes a custom outbound email + a tailored resume, and queues it all in Gmail —
then follows up automatically.

> Built with Python + [n8n](https://n8n.io). LLM, email-finding, and
> company-resolution are all swappable. Runs locally and free (apart from
> optional LLM credits).

---

## What it does

```
Scrape GTM jobs (LinkedIn US/UK, full JDs)
      │
      ▼
Dedupe to one role per company  ──►  Resolve company domain (Clearbit)
      │
      ▼
Estimate company size from the JD  ──►  skip enterprises (focus on startups)
      │
      ▼
Find the decision-maker + verified email   (Hunter.io)
      │
      ▼
Research their GTM from the JD + site, write an outbound email   (LLM)
      │
      ▼
Generate a role-tailored one-page resume → PDF   (LLM + headless Chrome)
      │
      ▼
Draft / send via Gmail   ──►   log to Google Sheet   ──►   auto follow-up
```

## Highlights

- **Multi-signal enrichment** — company domain via Clearbit, decision-maker +
  verified email via Hunter, company-size estimate via LLM (to skip enterprises
  where founder outreach doesn't land).
- **JD-grounded personalization** — every email is written from the actual job
  description: it infers the company's stack and the gap they're hiring to fill,
  then pitches a specific outbound play. Strictly outbound, never pitches a
  company its own product.
- **Tailored resumes** — a one-page resume is regenerated per role from a single
  source-of-truth profile, rendered to PDF.
- **Deliverability-aware** — built by someone who runs SPF/DKIM/DMARC and
  multi-domain cold-email infrastructure; volume is throttled and confidence-gated.
- **Self-correcting pipeline** — dedupes against a Google Sheet, retries on rate
  limits, and follows up only with people who haven't replied.

## Stack

| Layer | Tool |
|---|---|
| Scraping | Python (`requests`, `BeautifulSoup`) — LinkedIn guest + jobPosting endpoints |
| Orchestration | n8n (self-hosted) |
| Company domain | Clearbit autocomplete |
| Contact + email | Hunter.io |
| AI (research, email, resume) | Pluggable — Claude / Groq / Gemini |
| Resume → PDF | Headless Chrome |
| Tracking | Google Sheets |
| Sending + follow-up | Gmail |

## Repo layout

```
scraper.py                              # multi-source GTM job scraper (full JDs + domains)
outreach/
  profile.md                           # single source of truth for resumes + emails
  resume_template.html                 # styled one-page resume template
  dashboard.html                       # self-contained outreach dashboard (load a CSV)
  workflows/
    1_gtm_outreach_pipeline.template.json   # main n8n pipeline (add your own keys)
    2_followup_engine.template.json         # reply detection + follow-ups
  SOP.md                               # step-by-step setup guide (non-technical)
  README.md                            # system overview
```

## Setup

See [`outreach/SOP.md`](outreach/SOP.md) for the full walkthrough. In short: run
the scraper, import the two n8n workflow templates, add your own Hunter / LLM /
Google credentials, point it at a tracking sheet, and run.

> The published workflow files are **templates** — replace `YOUR_HUNTER_API_KEY`
> and `YOUR_GOOGLE_SHEET_ID` with your own before importing.
