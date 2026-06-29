import asyncio
import csv
from datetime import datetime
from urllib.parse import urljoin
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

START_URL = "https://careers.bcg.com/global/en/search-results"
BASE_URL  = "https://careers.bcg.com"
CSV_FILE  = "bcg_kenya_jobs.csv"

# Toggle if you want card teaser descriptions (outerHTML -> text). Set False for max speed.
INCLUDE_DESCRIPTION = True


def parse_iso_or_date(raw: str) -> str:
    """
    Accepts ISO-like strings (e.g., 2024-05-27T00:00:00.000+0000) or common date text.
    Returns YYYY-MM-DD if parse succeeds; else raw.
    """
    if not raw:
        return ""
    raw = raw.strip()
    # ISO with timezone
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Month-name formats fallback
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw


async def extract_job_from_card(card):
    """
    Extract job data from a single LI.jobs-list-item element.
    Uses data-ph-at-* attributes first; falls back to visible text.
    """
    # Main job anchor that holds structured attributes
    job_anchor = card.locator("[data-ph-at-id='job-link']")
    apply_anchor = card.locator("[data-ph-at-id='apply-link']")

    # Pull structured attrs (fast; no DOM text juggling)
    title_attr      = await job_anchor.get_attribute("data-ph-at-job-title-text") or ""
    location_attr   = await job_anchor.get_attribute("data-ph-at-job-location-text") or ""
    category_attr   = await job_anchor.get_attribute("data-ph-at-job-category-text") or ""
    job_id_attr     = await job_anchor.get_attribute("data-ph-at-job-id-text") or ""
    job_type_attr   = await job_anchor.get_attribute("data-ph-at-job-type-text") or ""
    post_date_attr  = await job_anchor.get_attribute("data-ph-at-job-post-date-text") or ""

    # Links
    detail_href = await job_anchor.get_attribute("href") or ""
    apply_href  = await apply_anchor.get_attribute("href") if await apply_anchor.count() else ""

    detail_link = urljoin(BASE_URL, detail_href)
    apply_link  = urljoin(BASE_URL, apply_href) if apply_href else detail_link  # fallback

    # Optional teaser description (cheap text grab)
    description = ""
    if INCLUDE_DESCRIPTION:
        desc_loc = card.locator("[data-ph-at-id='jobdescription-text']")
        if await desc_loc.count():
            description = (await desc_loc.inner_text()).strip()

    # Parse posting date
    post_date = parse_iso_or_date(post_date_attr)

    # Fallbacks if attrs missing: visible text spans
    if not title_attr:
        title_attr = (await card.locator(".job-title span, span[au-target-id]").first.inner_text()).strip() if await card.locator(".job-title span, span[au-target-id]").count() else ""
    if not location_attr:
        loc_loc = card.locator(".job-location")
        if await loc_loc.count():
            location_attr = (await loc_loc.inner_text()).strip()
    if not category_attr:
        cat_loc = card.locator(".job-category")
        if await cat_loc.count():
            category_attr = (await cat_loc.inner_text()).strip()

    return {
        "Title": title_attr.strip(),
        "Location": location_attr.strip(),
        "Category": category_attr.strip(),
        "Job ID": job_id_attr.strip(),
        "Job Type": job_type_attr.strip(),
        "Post Date": post_date,
        "Description": description.strip(),
        "Detail Link": detail_link.strip(),
        "Apply Link": apply_link.strip(),
    }


async def scrape_bcg_jobs():
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # change to True when stable
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Navigating to BCG Global search...")
        await page.goto(START_URL, timeout=90000)

        # Some sessions show a marketing overlay — ignore if not there
        try:
            await page.wait_for_selector("#pop-div08146447446432217", state="detached", timeout=5000)
            print("✅ Overlay dismissed (or not present).")
        except PlaywrightTimeoutError:
            print("⚠️ Overlay not gone after 5s; proceeding anyway...")

        page_num = 1
        total_scraped = 0

        while True:
            # Wait for job cards on current page
            try:
                await page.wait_for_selector("li.jobs-list-item", timeout=30000)
            except PlaywrightTimeoutError:
                print(f"⚠️ Timeout waiting for job cards on page {page_num}. Stopping.")
                break

            job_cards = await page.locator("li.jobs-list-item").all()
            print(f"📄 Page {page_num}: {len(job_cards)} job card(s) detected.")

            for card in job_cards:
                data = await extract_job_from_card(card)

                # Kenya filter
                if "kenya" not in data["Location"].lower():
                    continue

                results.append(data)
                total_scraped += 1
                print(f"✅ {data['Title']} | {data['Location']}")

            # Pagination: look for a visible/enabled next button
            # Different implementations exist; try a few selectors.
            next_btn = page.locator("a.pagination-next, button[aria-label='Next Page'], a[aria-label='Next']")
            if await next_btn.count() == 0:
                break

            # Confirm it's enabled/visible
            try:
                if not await next_btn.is_enabled():
                    break
                await next_btn.click()
                page_num += 1
                await page.wait_for_timeout(2000)  # allow DOM swap
            except Exception:
                break

        await context.close()
        await browser.close()

    # Save CSV
    fieldnames = [
        "Title", "Location", "Category", "Job ID", "Job Type",
        "Post Date", "Description", "Detail Link", "Apply Link"
    ]
    with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n📁 Saved {len(results)} Kenya job(s) to {CSV_FILE}.")


if __name__ == "__main__":
    asyncio.run(scrape_bcg_jobs())
