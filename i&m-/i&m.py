import asyncio
import csv
import re
from urllib.parse import urljoin
from typing import List, Tuple, Dict
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError, Page

BASE_URL = "https://imbank.bamboohr.com"
CAREERS_URL = f"{BASE_URL}/careers"
CSV_FILE = "imbank_nairobi_jobs.csv"
HEADLESS = True
NAV_TIMEOUT = 60_000  # ms


# ---------------- Utilities ---------------- #
async def scroll_all(page: Page, step: int = 1000, pause_ms: int = 300) -> None:
    """Scroll to bottom to trigger lazy-load job listings."""
    prev_height = 0
    while True:
        await page.evaluate(f"window.scrollBy(0, {step});")
        await page.wait_for_timeout(pause_ms)
        height = await page.evaluate("() => document.body.scrollHeight")
        if height == prev_height:
            break
        prev_height = height


async def collect_job_links_from_page(page: Page) -> List[str]:
    """Collect candidate job detail links from all anchors."""
    hrefs = await page.eval_on_selector_all("a", "els => els.map(e => e.getAttribute('href'))")
    links = []
    for href in hrefs:
        if href and href.startswith("/careers/") and len(href) > len("/careers/"):
            full = urljoin(BASE_URL, href)
            links.append(full)

    # Remove duplicates while preserving order
    seen, dedup = set(), []
    for link in links:
        if link not in seen:
            seen.add(link)
            dedup.append(link)
    return dedup


async def safe_get_text(page: Page, selector: str) -> str:
    loc = page.locator(selector)
    if await loc.count():
        return (await loc.inner_text()).strip()
    return ""


async def extract_job_fields(detail_page: Page) -> Tuple[str, str, str, str]:
    """Extract Title, Location, Job Type, Department from job detail page."""

    # Title
    title = (
        await safe_get_text(detail_page, "h3.jss-g37") or
        await safe_get_text(detail_page, "h1") or
        "N/A"
    )

    # Location
    location = (
        await safe_get_text(detail_page, "[data-automation-id='res_ats_jobLocation']") or
        await safe_get_text(detail_page, ".ResAts__jobLocation") or
        "N/A"
    )
    if location == "N/A":
        body_txt = await detail_page.inner_text("body")
        match = re.search(r"(Nairobi[^,\n]*[, ]*(?:Kenya)?)", body_txt, flags=re.I)
        if match:
            location = match.group(1).strip()

    # Job Type
    job_type = await safe_get_text(detail_page, "p.jss-g66.jss-g72") or "N/A"

    # Department
    department = await safe_get_text(detail_page, "p.jss-g66.jss-g70") or "N/A"

    return title, location, job_type, department


# ---------------- Main Scraper ---------------- #
async def scrape_imbank_jobs() -> None:
    results: List[Dict[str, str]] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context()
        page = await context.new_page()

        print(f"🌍 Navigating to {CAREERS_URL}")
        await page.goto(CAREERS_URL, timeout=NAV_TIMEOUT)

        # Scroll to load all jobs
        await scroll_all(page)

        try:
            await page.wait_for_selector('a[href^="/careers/"]', timeout=15_000)
        except PWTimeoutError:
            print("⚠️ Could not confirm job links; continuing...")

        job_links = await collect_job_links_from_page(page)
        print(f"🔗 Found {len(job_links)} potential job(s).")

        for idx, link in enumerate(job_links, start=1):
            print(f"➡️ Opening job {idx}/{len(job_links)}: {link}")
            detail = await context.new_page()
            try:
                await detail.goto(link, timeout=NAV_TIMEOUT)
                try:
                    await detail.wait_for_selector("h3.jss-g37, h1", timeout=10_000)
                except PWTimeoutError:
                    print("   ⚠️ No clear job title; scraping anyway.")

                title, location, job_type, department = await extract_job_fields(detail)

                if "nairobi" in location.lower():
                    results.append({
                        "Title": title,
                        "Location": location,
                        "Job Type": job_type,
                        "Department": department,
                        "Apply Link": link
                    })
                    print(f"   ✅ {title} | {location} | {job_type} | {department}")
                else:
                    print(f"   ⏭ Skipped (not Nairobi): {title} | {location}")

            except Exception as e:
                print(f"   ❌ Error scraping {link}: {e}")
            finally:
                await detail.close()

        await context.close()
        await browser.close()

    # Save CSV
    with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Job Type", "Department", "Apply Link"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n📁 Saved {len(results)} Nairobi-based job(s) to {CSV_FILE}.")


# ---------------- Entry ---------------- #
if __name__ == "__main__":
    asyncio.run(scrape_imbank_jobs())
