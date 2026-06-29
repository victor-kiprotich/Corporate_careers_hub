import asyncio
import csv
from urllib.parse import urljoin
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = "https://sunking.com/careers/"
CSV_FILE = "sun_king_jobs_kenya.csv"
MAX_CONCURRENT = 5  # limit concurrency to avoid browser overload


async def scrape_detail(context, job):
    """Scrape details from an individual job page."""
    title, link = job["title"], job["link"]

    detail_page = await context.new_page()
    try:
        await detail_page.goto(link, timeout=30000)
        await detail_page.wait_for_selector("div.JobListing-title", timeout=15000)

        async def safe_text(selector):
            loc = detail_page.locator(selector)
            return (await loc.inner_text()).strip() if await loc.count() else ""

        location = await safe_text("div.JobListing-location p")
        department = await safe_text("div.JobListing-department p")
        job_type = await safe_text("div.JobListing-employement_type p")

        return {
            "Title": title,
            "Location": location,
            "Department": department,
            "Employment Type": job_type,
            "Apply Link": link,
        }
    except PlaywrightTimeoutError:
        print(f"⚠️ Timeout scraping {title}")
        return None
    finally:
        await detail_page.close()


async def scrape_sun_king_jobs():
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Navigating to Sun King Careers...")
        await page.goto(BASE_URL, timeout=60000)

        print("🔍 Clicking 'View All Job Vacancies'...")
        await page.get_by_role("link", name="View All Job Vacancies").click()

        # Wait for jobs to load
        await page.wait_for_selector("p.listing-title", timeout=60000)

        job_cards = page.locator("a:has(p.listing-title)")
        total = await job_cards.count()
        print(f"✅ Found {total} job listing card(s).")

        jobs = []
        for i in range(total):
            title = (await job_cards.nth(i).locator("p.listing-title").inner_text()).strip()
            href = await job_cards.nth(i).get_attribute("href")
            full_url = href if href.startswith("http") else urljoin(BASE_URL, href.lstrip("./"))
            jobs.append({"title": title, "link": full_url})

        print(f"📦 Loaded {len(jobs)} jobs. Now scraping details...")

        # Concurrent scraping with a semaphore
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)

        async def bounded_scrape(job):
            async with semaphore:
                return await scrape_detail(context, job)

        detail_tasks = [bounded_scrape(job) for job in jobs]
        details = await asyncio.gather(*detail_tasks)

        # Filter Kenya jobs
        kenya_jobs = [job for job in details if job and "kenya" in job["Location"].lower()]

        print(f"✅ Found {len(kenya_jobs)} Kenya jobs.")

        # Save to CSV
        with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["Title", "Location", "Department", "Employment Type", "Apply Link"],
            )
            writer.writeheader()
            writer.writerows(kenya_jobs)

        print(f"\n📁 Saved {len(kenya_jobs)} Kenya jobs to {CSV_FILE}.")

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(scrape_sun_king_jobs())
