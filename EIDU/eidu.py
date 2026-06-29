import asyncio
import csv
from typing import List, Dict, Union
from playwright.async_api import async_playwright, Page, Frame, TimeoutError as PlaywrightTimeoutError

BASE_URL = "https://eidu.jobs.personio.com"
JOBS_URL = f"{BASE_URL}/?filters=eyJvZmZpY2VfaWQiOlszMjY1MTMwXX0="
CSV_FILE = "eidu_kenya_jobs.csv"
HEADLESS = True
NAV_TIMEOUT = 60_000


async def get_jobs_context(page: Page) -> Union[Page, Frame]:
    """Return iframe context if present, else main page."""
    await page.wait_for_load_state("domcontentloaded")
    await page.wait_for_timeout(500)

    iframe = page.locator("iframe[src*='personio']")
    if await iframe.count():
        try:
            frame_el = await iframe.first.element_handle()
            frame = await frame_el.content_frame()
            if frame:
                return frame
        except:
            pass
    return page


async def scrape_listing(dom_ctx: Union[Page, Frame]) -> List[Dict[str, str]]:
    """Scrape job data from listing without opening detail pages."""
    selector = "a.job-box-link.filtered-position"
    try:
        await dom_ctx.wait_for_selector(selector, timeout=20_000)
    except PlaywrightTimeoutError:
        print("⚠️ No job listings found.")
        return []

    jobs = []
    anchors = dom_ctx.locator(selector)
    count = await anchors.count()
    print(f"🔗 Found {count} job(s).")

    for i in range(count):
        a = anchors.nth(i)

        # Job link
        href = await a.get_attribute("href") or ""
        link = href if href.startswith("http") else BASE_URL + href

        # Title
        title_el = a.locator(".jb-title")
        title = (await title_el.inner_text()).strip() if await title_el.count() else \
                (await a.get_attribute("data-job-position-name") or "").strip()

        # Job Type
        job_type = (await a.get_attribute("data-job-position-employment") or "").strip()
        if not job_type:
            desc_first_span = a.locator(".jb-description span").first
            if await desc_first_span.count():
                job_type = (await desc_first_span.inner_text()).strip()

        # Location
        location = (await a.get_attribute("data-job-position-office") or "").strip()
        if not location:
            desc_text = ""
            desc_block = a.locator(".jb-description")
            if await desc_block.count():
                desc_text = (await desc_block.inner_text()).strip()
                if "·" in desc_text:
                    location = desc_text.split("·", 1)[1].strip()
                else:
                    location = desc_text

        location = " ".join(location.split()).lstrip(", ")

        jobs.append({
            "Title": title,
            "Link": link,
            "Location": location,
            "Job Type": job_type
        })

    return jobs


async def scrape_eidu_jobs():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Navigating to EIDU Kenya jobs page...")
        await page.goto(JOBS_URL, timeout=NAV_TIMEOUT)

        dom_ctx = await get_jobs_context(page)
        jobs = await scrape_listing(dom_ctx)

        await context.close()
        await browser.close()

    if jobs:
        with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["Title", "Link", "Location", "Job Type"])
            writer.writeheader()
            writer.writerows(jobs)
        print(f"\n✅ Saved {len(jobs)} job(s) to {CSV_FILE}.")
    else:
        print("\n⚠️ No jobs scraped.")


if __name__ == "__main__":
    asyncio.run(scrape_eidu_jobs())
