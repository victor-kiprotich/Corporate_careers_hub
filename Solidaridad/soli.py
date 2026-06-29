import asyncio
import csv
import re
from urllib.parse import urljoin
from typing import List, Dict, Tuple

from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError, Page

BASE_URL = "https://solidaridadnetworkeca.bamboohr.com"
CAREERS_URL = f"{BASE_URL}/careers"
CSV_FILE = "solidaridad_jobs.csv"
HEADLESS = True
NAV_TIMEOUT = 60_000


# ---------------- Utility Functions ---------------- #
async def scroll_all(page: Page, step=1000, pause_ms=300):
    """Scroll to bottom to load all jobs (BambooHR often lazy-loads)."""
    prev_height = 0
    while True:
        await page.evaluate(f"window.scrollBy(0, {step});")
        await page.wait_for_timeout(pause_ms)
        height = await page.evaluate("() => document.body.scrollHeight")
        if height == prev_height:
            break
        prev_height = height


async def collect_job_links(page: Page) -> List[str]:
    """Collect job detail links (BambooHR jobs have /careers/ in href)."""
    hrefs = await page.eval_on_selector_all("a", "els => els.map(e => e.getAttribute('href'))")
    links = []
    for href in hrefs:
        if href and href.startswith("/careers/") and len(href) > len("/careers/"):
            links.append(urljoin(BASE_URL, href))

    # Deduplicate
    seen, dedup = set(), []
    for link in links:
        if link not in seen:
            seen.add(link)
            dedup.append(link)
    return dedup


async def safe_get_text(page: Page, selector: str) -> str:
    """Get text content safely from first matching element."""
    loc = page.locator(selector)
    count = await loc.count()
    if count > 0:
        return (await loc.nth(0).inner_text()).strip()
    return ""


async def extract_job_fields(detail_page: Page) -> Tuple[str, str, str, str]:
    """
    Extract Title, Location, Job Type, Department from job detail page.
    Solidaridad uses custom CSS classes for title and details.
    """

    # ✅ Title (specific h3 class to avoid strict mode errors)
    title = (
        await safe_get_text(detail_page, "h3.jss-g20") or
        await safe_get_text(detail_page, "[data-automation-id='res_ats_jobTitle']") or
        "N/A"
    )

    # ✅ Location
    location = (
        await safe_get_text(detail_page, "[data-automation-id='res_ats_jobLocation']") or
        await safe_get_text(detail_page, ".ResAts__jobLocation") or ""
    )
    if not location:
        body = await detail_page.inner_text("body")
        match = re.search(r"(Nairobi|Kampala|Dar es Salaam|Kenya|Uganda|Tanzania)", body, flags=re.I)
        if match:
            location = match.group(1)

    # ✅ Job Type
    job_type = (
        await safe_get_text(detail_page, "p.jss-g66.jss-g72") or
        await safe_get_text(detail_page, "[data-automation-id='res_ats_jobEmploymentType']") or
        "N/A"
    )

    # ✅ Department
    department = (
        await safe_get_text(detail_page, "p.jss-g66.jss-g70") or
        "N/A"
    )

    return title, (location or "N/A"), job_type, department


# ---------------- Main Scraper ---------------- #
async def scrape_solidaridad_jobs():
    results: List[Dict[str, str]] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context()
        page = await context.new_page()

        print(f"🌍 Opening {CAREERS_URL}")
        await page.goto(CAREERS_URL, timeout=NAV_TIMEOUT)

        await scroll_all(page)

        try:
            await page.wait_for_selector('a[href^="/careers/"]', timeout=15000)
        except PWTimeoutError:
            print("⚠️ Could not find job links quickly. Proceeding anyway.")

        job_links = await collect_job_links(page)
        print(f"🔗 Found {len(job_links)} job(s).")

        for idx, link in enumerate(job_links, start=1):
            print(f"➡️ Opening job {idx}/{len(job_links)}: {link}")
            detail = await context.new_page()
            try:
                await detail.goto(link, timeout=NAV_TIMEOUT)
                try:
                    await detail.wait_for_selector("h3.jss-g20, h1, [data-automation-id='res_ats_jobTitle']", timeout=10000)
                except PWTimeoutError:
                    print("   ⚠️ No clear job title; scraping anyway.")

                title, location, job_type, department = await extract_job_fields(detail)

                results.append({
                    "Title": title,
                    "Location": location,
                    "Job Type": job_type,
                    "Department": department,
                    "Apply Link": link
                })
                print(f"   ✅ {title} | {location} | {job_type} | {department}")

            except Exception as e:
                print(f"   ❌ Error scraping {link}: {e}")
            finally:
                await detail.close()

        await context.close()
        await browser.close()

    # Save to CSV
    with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Job Type", "Department", "Apply Link"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n📁 Saved {len(results)} job(s) to {CSV_FILE}")


# ---------------- Entry ---------------- #
if __name__ == "__main__":
    asyncio.run(scrape_solidaridad_jobs())
