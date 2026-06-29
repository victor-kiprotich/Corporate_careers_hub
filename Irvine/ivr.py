import asyncio
import csv
import re
from urllib.parse import urljoin
from typing import List, Tuple, Dict
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError, Page

BASE_URL = "https://irvinepartners.bamboohr.com"
CAREERS_URL = f"{BASE_URL}/careers"
CSV_FILE = "irvinepartners_jobs.csv"
HEADLESS = True
NAV_TIMEOUT = 60_000  # ms


# ---------------- Utilities ---------------- #
async def scroll_all(page: Page, step: int = 1000, pause_ms: int = 300) -> None:
    """Scroll to bottom to load all jobs (if lazy-loaded)."""
    prev_height = 0
    while True:
        await page.evaluate(f"window.scrollBy(0, {step});")
        await page.wait_for_timeout(pause_ms)
        height = await page.evaluate("() => document.body.scrollHeight")
        if height == prev_height:
            break
        prev_height = height


async def collect_job_links(page: Page) -> List[str]:
    """Collect job links starting with /careers/."""
    hrefs = await page.eval_on_selector_all("a", "els => els.map(e => e.getAttribute('href'))")
    links = [urljoin(BASE_URL, h) for h in hrefs if h and h.startswith("/careers/") and len(h) > len("/careers/")]
    return list(dict.fromkeys(links))  # deduplicate preserving order


async def safe_get_text(page: Page, selector: str) -> str:
    loc = page.locator(selector)
    if await loc.count():
        return (await loc.inner_text()).strip()
    return ""


async def extract_job_fields(detail_page: Page) -> Tuple[str, str, str]:
    """Extract Title, Location, Job Type for Irvine Partners."""
    # ✅ Job Title (Irvine uses h1 on job page)
    title = (
        await safe_get_text(detail_page, "h1") or
        await safe_get_text(detail_page, "h2") or
        "N/A"
    )

    # ✅ Location: Look for "Location" label or fallback regex
    location = await safe_get_text(detail_page, "text=Location >> xpath=following-sibling::*[1]")
    if not location:
        body = await detail_page.inner_text("body")
        match = re.search(r"(Cape Town|Johannesburg|London|Nairobi)", body, flags=re.I)
        if match:
            location = match.group(1)

    # ✅ Job Type: Look for "Employment Type" or bullet list
    job_type = await safe_get_text(detail_page, "text=Employment Type >> xpath=following-sibling::*[1]")
    if not job_type:
        # Fallback: check visible bullet points for Full-time/Part-time
        bullets = detail_page.locator("ul li")
        count = await bullets.count()
        for i in range(count):
            txt = (await bullets.nth(i).inner_text()).strip()
            if any(k in txt.lower() for k in ["full-time", "part-time", "contract"]):
                job_type = txt
                break

    return title, (location or "N/A"), (job_type or "N/A")


# ---------------- Main Scraper ---------------- #
async def scrape_irvine_jobs():
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
                    await detail.wait_for_selector("h1", timeout=10000)
                except PWTimeoutError:
                    print("   ⚠️ No clear job title; scraping anyway.")

                title, location, job_type = await extract_job_fields(detail)

                results.append({
                    "Title": title,
                    "Location": location,
                    "Job Type": job_type,
                    "Apply Link": link
                })
                print(f"   ✅ {title} | {location} | {job_type}")

            except Exception as e:
                print(f"   ❌ Error scraping {link}: {e}")
            finally:
                await detail.close()

        await context.close()
        await browser.close()

    # ✅ Save CSV
    with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Job Type", "Apply Link"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n📁 Saved {len(results)} job(s) to {CSV_FILE}")


if __name__ == "__main__":
    asyncio.run(scrape_irvine_jobs())
