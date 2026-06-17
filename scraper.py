"""
GTM Engineer Remote Job Scraper
Scrapes remote GTM (Go-To-Market) engineer jobs from multiple sources.
Targets: USA and UK locations.

Sources:
  1. RemoteOK (public JSON API)
  2. Adzuna (free API — requires API key)
  3. LinkedIn (public job search — limited, no auth)
  4. Arbeitnow (public JSON API)

Output: CSV with job description, company, position, website, LinkedIn URL.
"""

import csv
import json
import random
import re
import time
import urllib.parse
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

SEARCH_TERMS = [
    "GTM engineer",
    "go to market engineer",
    "GTM solutions engineer",
    "GTM technical",
]

LOCATIONS = ["USA", "UK", "United States", "United Kingdom", "Remote"]


@dataclass
class Job:
    position: str = ""
    company: str = ""
    job_description: str = ""
    company_website: str = ""
    company_domain: str = ""
    company_linkedin: str = ""
    company_headcount: str = ""
    decision_maker_name: str = ""
    decision_maker_linkedin: str = ""
    location: str = ""
    source: str = ""
    url: str = ""
    date_scraped: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))


# ---------------------------------------------------------------------------
# Source 1: RemoteOK — free public JSON API
# ---------------------------------------------------------------------------
def scrape_remoteok() -> list[Job]:
    print("[RemoteOK] Scraping...")
    jobs = []
    url = "https://remoteok.com/api"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            data = data[1:]  # first element is metadata
        for item in data:
            title = item.get("position", "")
            desc = item.get("description", "")
            combined = f"{title} {desc}".lower()
            if not any(term.lower() in combined for term in SEARCH_TERMS):
                continue
            location = item.get("location", "")
            jobs.append(Job(
                position=title,
                company=item.get("company", ""),
                job_description=_clean_html(desc)[:2000],
                company_website=item.get("company_logo", ""),  # often has domain
                company_linkedin=_guess_linkedin(item.get("company", "")),
                location=location or "Remote",
                source="RemoteOK",
                url=item.get("url", ""),
            ))
    except Exception as e:
        print(f"  [RemoteOK] Error: {e}")
    print(f"  [RemoteOK] Found {len(jobs)} jobs")
    return jobs


# ---------------------------------------------------------------------------
# Source 2: Arbeitnow — free public JSON API (remote-friendly)
# ---------------------------------------------------------------------------
def scrape_arbeitnow() -> list[Job]:
    print("[Arbeitnow] Scraping...")
    jobs = []
    for page in range(1, 4):
        url = f"https://www.arbeitnow.com/api/job-board-api?page={page}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("data", []):
                title = item.get("title", "")
                desc = item.get("description", "")
                combined = f"{title} {desc}".lower()
                if not any(term.lower() in combined for term in SEARCH_TERMS):
                    continue
                if not item.get("remote", False):
                    continue
                location = item.get("location", "")
                jobs.append(Job(
                    position=title,
                    company=item.get("company_name", ""),
                    job_description=_clean_html(desc)[:2000],
                    company_website=item.get("url", ""),
                    company_linkedin=_guess_linkedin(item.get("company_name", "")),
                    location=location or "Remote",
                    source="Arbeitnow",
                    url=item.get("url", ""),
                ))
            if not data.get("links", {}).get("next"):
                break
        except Exception as e:
            print(f"  [Arbeitnow] Error: {e}")
            break
        time.sleep(1)
    print(f"  [Arbeitnow] Found {len(jobs)} jobs")
    return jobs


# ---------------------------------------------------------------------------
# Source 3: LinkedIn public job search (paginated, multiple queries)
# ---------------------------------------------------------------------------

LINKEDIN_QUERIES = [
    "GTM engineer",
    "GTM engineer remote",
    "go to market engineer",
    "go-to-market engineer",
    "GTM solutions engineer",
    "GTM technical engineer",
    "GTM systems engineer",
    "GTM ops engineer",
    "GTM platform engineer",
    "GTM automation engineer",
    "GTM data engineer",
    "revenue engineer GTM",
    "sales engineer GTM",
    "growth engineer GTM",
]

LINKEDIN_LOCATIONS = [
    ("103644278", "United States"),
    ("101165590", "United Kingdom"),
]

MAX_PAGES_PER_QUERY = 3  # 25 results per page → up to 75 per query/location
FETCH_DESCRIPTIONS = True  # pull full JDs at scrape time (robust: jobPosting API + retry/backoff)
ENRICH_COMPANIES = False  # headcount/decision-maker scraping; superseded by Apollo in the n8n pipeline

# Rotate realistic browser UAs to dodge LinkedIn throttling
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


def _browser_headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.linkedin.com/jobs/",
    }


def _get_with_retry(url: str, max_retries: int = 4, base_sleep: float = 2.0):
    """GET with rotating UA and exponential backoff on 429/403/999 (LinkedIn throttling)."""
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=_browser_headers(), timeout=25)
        except Exception:
            time.sleep(base_sleep * (attempt + 1))
            continue
        if resp.status_code == 200:
            return resp
        if resp.status_code in (429, 403, 999):
            wait = min(base_sleep * (2 ** attempt) + random.uniform(0, 2), 60)
            time.sleep(wait)
            continue
        return resp
    return None


def _extract_job_id(job_url: str) -> str:
    ids = re.findall(r"(\d{6,})", job_url or "")
    return ids[-1] if ids else ""


def _resolve_domain(company: str) -> str:
    """Resolve a company name to its primary domain via Clearbit autocomplete.
    Retries with backoff because Clearbit rate-limits when hit rapidly at scale."""
    if not company:
        return ""
    for attempt in range(3):
        try:
            resp = requests.get(
                "https://autocomplete.clearbit.com/v1/companies/suggest",
                params={"query": company},
                headers={"User-Agent": random.choice(USER_AGENTS)},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                return (data[0].get("domain") or "") if data else ""
            time.sleep(2 * (attempt + 1) + random.uniform(0, 1))  # backoff on 429/etc.
        except Exception:
            time.sleep(2 * (attempt + 1))
    return ""


def _domain_from_linkedin(linkedin_url: str) -> str:
    """Fallback: pull a company's website (→domain) from its LinkedIn About page."""
    if not linkedin_url or "linkedin.com/company" not in linkedin_url:
        return ""
    base = linkedin_url.split("?")[0].rstrip("/")
    for url in (base + "/about/", base):
        resp = _get_with_retry(url, max_retries=3)
        if not resp or resp.status_code != 200:
            continue
        soup = BeautifulSoup(resp.text, "html.parser")
        link = soup.find("a", {"data-tracking-control-name": "about_website"})
        href = link["href"] if link and link.get("href") else ""
        if not href:  # any external (non-linkedin) link as a loose fallback
            for a in soup.find_all("a", href=True):
                h = a["href"]
                if h.startswith("http") and "linkedin.com" not in h and "/redir/" not in h:
                    href = h
                    break
        if not href:
            continue
        if "redir/redirect" in href:  # unwrap LinkedIn's redirect wrapper
            qs = urllib.parse.urlparse(href).query
            href = urllib.parse.parse_qs(qs).get("url", [""])[0]
        netloc = urllib.parse.urlparse(href).netloc or href
        domain = netloc.replace("www.", "").strip().strip("/")
        if "." in domain and " " not in domain:
            return domain
    return ""


def _fetch_linkedin_page(query: str, geo_id: str, location: str, start: int) -> list[dict]:
    url = (
        "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        f"?keywords={urllib.parse.quote(query)}"
        f"&location={urllib.parse.quote(location)}"
        f"&geoId={geo_id}"
        "&f_WT=2"
        f"&start={start}"
    )
    resp = requests.get(url, headers=HEADERS, timeout=30)
    if resp.status_code != 200:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.find_all("div", class_="base-card")
    results = []
    for card in cards:
        title_el = card.find("h3", class_="base-search-card__title")
        company_el = card.find("h4", class_="base-search-card__subtitle")
        link_el = card.find("a", class_="base-card__full-link")
        loc_el = card.find("span", class_="job-search-card__location")
        title = title_el.get_text(strip=True) if title_el else ""
        company = company_el.get_text(strip=True) if company_el else ""
        job_url = link_el["href"] if link_el and link_el.get("href") else ""
        loc = loc_el.get_text(strip=True) if loc_el else location
        if title:
            results.append({
                "title": title,
                "company": company,
                "url": job_url.split("?")[0] if job_url else "",
                "location": loc,
            })
    return results


def _fetch_linkedin_description(job_url: str) -> tuple[str, str]:
    """Fetch full JD + company LinkedIn URL. Tries the lighter jobPosting guest
    endpoint first (more permissive), then falls back to the full job-view page."""
    job_id = _extract_job_id(job_url)
    candidates = []
    if job_id:
        candidates.append(
            f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
        )
    if job_url:
        candidates.append(job_url)

    for url in candidates:
        resp = _get_with_retry(url)
        if not resp or resp.status_code != 200:
            continue
        soup = BeautifulSoup(resp.text, "html.parser")
        desc_div = (
            soup.find("div", class_="show-more-less-html__markup")
            or soup.find("div", class_="description__text")
        )
        if not desc_div:
            continue
        text = desc_div.get_text(separator="\n", strip=True)
        text = re.sub(r"\n{2,}", "\n", text).strip()
        if len(text) < 80:  # too short → probably a block page, try next candidate
            continue
        website = ""
        link_el = soup.find("a", class_="topcard__org-name-link")
        if link_el and link_el.get("href") and "linkedin.com/company" in link_el["href"]:
            website = link_el["href"].split("?")[0]
        return text[:5000], website
    return "", ""


def scrape_linkedin() -> list[Job]:
    print("[LinkedIn] Scraping (deep pagination across multiple queries)...")
    raw_results: list[dict] = []
    seen_urls = set()

    total_queries = len(LINKEDIN_QUERIES) * len(LINKEDIN_LOCATIONS)
    done = 0
    for query in LINKEDIN_QUERIES:
        for geo_id, location_name in LINKEDIN_LOCATIONS:
            done += 1
            print(f"  [{done}/{total_queries}] '{query}' in {location_name}...", end=" ")
            page_count = 0
            for page in range(MAX_PAGES_PER_QUERY):
                start = page * 25
                try:
                    cards = _fetch_linkedin_page(query, geo_id, location_name, start)
                except Exception:
                    break
                if not cards:
                    break
                for card in cards:
                    if card["url"] not in seen_urls:
                        seen_urls.add(card["url"])
                        raw_results.append(card)
                page_count += 1
                time.sleep(1.5)
            print(f"{page_count} pages")
            time.sleep(1)

    print(f"  [LinkedIn] {len(raw_results)} unique listings found.")

    # Dedup by company, keeping the strongest GTM-titled role — we only need one
    # job (and one JD fetch) per company for outreach.
    def _gtm_score(title: str) -> int:
        t = title.lower()
        if re.search(r"gtm engineer|go.?to.?market engineer", t):
            return 2
        if "gtm" in t or "go to market" in t or "go-to-market" in t:
            return 1
        return 0

    best_by_company: dict[str, dict] = {}
    for item in raw_results:
        co = item["company"].strip().lower()
        if not co:
            continue
        score = _gtm_score(item["title"])
        if score == 0:
            continue  # skip tangential non-GTM results
        if co not in best_by_company or score > best_by_company[co]["_score"]:
            best_by_company[co] = {**item, "_score": score}

    deduped = list(best_by_company.values())
    print(f"  [LinkedIn] {len(deduped)} unique GTM companies; fetching descriptions...")

    jobs = []
    got = 0
    for i, item in enumerate(deduped):
        desc, company_page = "", ""
        if FETCH_DESCRIPTIONS:
            desc, company_page = _fetch_linkedin_description(item["url"])
            if desc:
                got += 1
            if (i + 1) % 15 == 0:
                print(f"    ...{i + 1}/{len(deduped)} ({got} with JD)")
            time.sleep(random.uniform(0.7, 1.5))  # light throttle
        # NOTE: domain is resolved by Hunter (by company name) in the n8n pipeline,
        # so we no longer call Clearbit here — it was rate-limited and added ~15s/company.
        jobs.append(Job(
            position=item["title"],
            company=item["company"],
            job_description=desc or "(visit link for full description)",
            company_website="",
            company_domain="",
            company_linkedin=company_page or _guess_linkedin(item["company"]),
            location=item["location"],
            source="LinkedIn",
            url=item["url"],
        ))

    print(f"  [LinkedIn] {len(jobs)} companies, {got} with full descriptions")
    return jobs


# ---------------------------------------------------------------------------
# Source 4: Adzuna API (free tier — 250 requests/month)
# Requires ADZUNA_APP_ID and ADZUNA_API_KEY env vars.
# Sign up free at https://developer.adzuna.com/
# ---------------------------------------------------------------------------
def scrape_adzuna() -> list[Job]:
    import os
    app_id = os.environ.get("ADZUNA_APP_ID", "")
    api_key = os.environ.get("ADZUNA_API_KEY", "")
    if not app_id or not api_key:
        print("[Adzuna] Skipped — set ADZUNA_APP_ID and ADZUNA_API_KEY env vars.")
        print("  Sign up free at https://developer.adzuna.com/")
        return []
    print("[Adzuna] Scraping...")
    jobs = []
    countries = [("us", "USA"), ("gb", "UK")]
    for country_code, country_name in countries:
        for query in ["GTM engineer", "go to market engineer"]:
            url = (
                f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/1"
                f"?app_id={app_id}&app_key={api_key}"
                f"&results_per_page=50"
                f"&what={urllib.parse.quote(query)}"
                f"&where=remote"
                f"&content-type=application/json"
            )
            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                for item in data.get("results", []):
                    jobs.append(Job(
                        position=item.get("title", ""),
                        company=item.get("company", {}).get("display_name", ""),
                        job_description=item.get("description", "")[:2000],
                        company_website=item.get("redirect_url", ""),
                        company_linkedin=_guess_linkedin(
                            item.get("company", {}).get("display_name", "")
                        ),
                        location=item.get("location", {}).get("display_name", country_name),
                        source="Adzuna",
                        url=item.get("redirect_url", ""),
                    ))
            except Exception as e:
                print(f"  [Adzuna] Error for {country_name}: {e}")
            time.sleep(1)
    print(f"  [Adzuna] Found {len(jobs)} jobs")
    return jobs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _clean_html(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def _guess_linkedin(company_name: str) -> str:
    if not company_name:
        return ""
    slug = re.sub(r"[^a-z0-9]+", "-", company_name.lower()).strip("-")
    return f"https://www.linkedin.com/company/{slug}"


# ---------------------------------------------------------------------------
# Enrichment: company headcount + founder/decision maker
# ---------------------------------------------------------------------------

_enrichment_cache: dict[str, dict] = {}


def _fetch_linkedin_company_page(company_slug: str) -> dict:
    """Scrape a LinkedIn public company page for headcount and website."""
    if company_slug in _enrichment_cache:
        return _enrichment_cache[company_slug]

    result = {"headcount": "", "website": ""}
    url = f"https://www.linkedin.com/company/{company_slug}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            _enrichment_cache[company_slug] = result
            return result
        text = resp.text
        headcount_match = re.search(
            r'(\d[\d,]*\s*-\s*\d[\d,]*)\s+employees', text
        ) or re.search(
            r'(\d[\d,]+)\s+employees', text
        ) or re.search(
            r'"staffCountRange":\s*"([^"]+)"', text
        ) or re.search(
            r'"staffCount":\s*(\d+)', text
        )
        if headcount_match:
            result["headcount"] = headcount_match.group(1).strip()
        soup = BeautifulSoup(text, "html.parser")
        website_link = soup.find("a", {"data-tracking-control-name": "about_website"})
        if website_link and website_link.get("href"):
            result["website"] = website_link["href"]
    except Exception:
        pass
    _enrichment_cache[company_slug] = result
    return result


def _search_decision_maker(company_name: str) -> tuple[str, str]:
    """Search for the founder/CEO LinkedIn profile of a company."""
    if not company_name:
        return "", ""

    engines = [
        (
            "https://html.duckduckgo.com/html/",
            {"q": f"{company_name} founder OR CEO site:linkedin.com/in/"},
            "post",
        ),
        (
            "https://www.bing.com/search",
            {"q": f"{company_name} founder OR CEO site:linkedin.com/in/"},
            "get",
        ),
    ]
    for url, params, method in engines:
        try:
            if method == "post":
                resp = requests.post(url, data=params, headers=HEADERS, timeout=15)
            else:
                resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                li_match = re.search(
                    r'(https?://\w+\.linkedin\.com/in/[^&?\"\s]+)', href
                )
                if li_match:
                    profile_url = li_match.group(1).rstrip("/")
                    name = ""
                    text = a_tag.get_text(separator=" ", strip=True)
                    name_match = re.match(
                        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', text
                    )
                    if name_match:
                        name = name_match.group(1)
                    if not name:
                        slug = profile_url.split("/in/")[-1].split("?")[0]
                        parts = slug.replace("-", " ").split()
                        name = " ".join(
                            p.capitalize() for p in parts if not p.isdigit()
                        )
                    return name, profile_url
        except Exception:
            continue
    return "", ""


def enrich_jobs(jobs: list[Job]) -> list[Job]:
    """Add headcount and decision maker info to each job."""
    companies_seen: dict[str, dict] = {}
    total = len(set(j.company for j in jobs if j.company))
    print(f"\n[Enrich] Enriching {total} unique companies with headcount + decision makers...")

    enriched = 0
    for job in jobs:
        if not job.company:
            continue
        company_key = job.company.lower().strip()

        if company_key in companies_seen:
            data = companies_seen[company_key]
            job.company_headcount = data["headcount"]
            job.decision_maker_name = data["dm_name"]
            job.decision_maker_linkedin = data["dm_linkedin"]
            if data.get("website") and not job.company_website:
                job.company_website = data["website"]
            continue

        enriched += 1
        if enriched % 25 == 1:
            print(f"  [Enrich] Processing company {enriched}/{total}...")

        slug = re.sub(r"[^a-z0-9]+", "-", company_key).strip("-")
        li_data = _fetch_linkedin_company_page(slug)

        dm_name, dm_linkedin = _search_decision_maker(job.company)

        data = {
            "headcount": li_data.get("headcount", ""),
            "website": li_data.get("website", ""),
            "dm_name": dm_name,
            "dm_linkedin": dm_linkedin,
        }
        companies_seen[company_key] = data

        job.company_headcount = data["headcount"]
        job.decision_maker_name = dm_name
        job.decision_maker_linkedin = dm_linkedin
        if data["website"] and not job.company_website:
            job.company_website = data["website"]

        time.sleep(1.5)

    print(f"  [Enrich] Done — enriched {enriched} companies")
    return jobs


def deduplicate(jobs: list[Job]) -> list[Job]:
    seen = set()
    unique = []
    for j in jobs:
        key = (j.position.lower().strip(), j.company.lower().strip())
        if key not in seen:
            seen.add(key)
            unique.append(j)
    return unique


def save_csv(jobs: list[Job], path: str) -> None:
    fieldnames = [
        "position", "company", "job_description", "company_website",
        "company_domain", "company_linkedin", "company_headcount",
        "decision_maker_name", "decision_maker_linkedin", "location",
        "source", "url", "date_scraped",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for job in jobs:
            writer.writerow(asdict(job))
    print(f"\nSaved {len(jobs)} jobs to {path}")


def save_json(jobs: list[Job], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([asdict(j) for j in jobs], f, indent=2, ensure_ascii=False)
    print(f"Saved {len(jobs)} jobs to {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("GTM Engineer Remote Job Scraper")
    print(f"Searching for: {', '.join(SEARCH_TERMS)}")
    print(f"Locations: USA, UK, Remote")
    print("=" * 60)
    print()

    all_jobs: list[Job] = []

    all_jobs.extend(scrape_remoteok())
    all_jobs.extend(scrape_arbeitnow())
    all_jobs.extend(scrape_linkedin())
    all_jobs.extend(scrape_adzuna())

    all_jobs = deduplicate(all_jobs)

    print(f"\nTotal unique jobs found: {len(all_jobs)}")

    if ENRICH_COMPANIES:
        all_jobs = enrich_jobs(all_jobs)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path.home() / "Desktop" / "GTM_Jobs"
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / f"gtm_jobs_{timestamp}.csv"
    json_path = output_dir / f"gtm_jobs_{timestamp}.json"

    save_csv(all_jobs, str(csv_path))
    save_json(all_jobs, str(json_path))

    print("\nSample results:")
    for job in all_jobs[:5]:
        print(f"  - {job.position} @ {job.company} ({job.source}) [{job.location}]")


if __name__ == "__main__":
    main()
