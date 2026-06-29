import asyncio
import pandas as pd
from urllib.parse import urljoin
from playwright.async_api import async_playwright

BASE_URL = "https://jobs.lever.co"
JOBS_URL = f"{BASE_URL}/tala?location=Nairobi"

async def scrape_job_detail(context, job_url):
    try:
        job_page = await context.new_page()
        await job_page.goto(job_url, timeout=60000)
        await job_page.wait_for_selector("h2", timeout=20000)

        # Job Title
        title = await job_page.locator("h2").text_content()

        # Location
        location_el = job_page.locator("div.sort-by-time.location")
        location = await location_el.text_content() if await location_el.count() > 0 else "N/A"

        # Category
        category_el = job_page.locator("div.sort-by-team.department")
        category = await category_el.text_content() if await category_el.count() > 0 else "N/A"

        await job_page.close()

        return {
            "Job Title": title.strip() if title else "N/A",
            "Location": location.strip(),
            "Category": category.strip(),
            "Apply Link": job_url
        }

    except Exception as e:
        print(f"❌ Error scraping job at {job_url}: {e}")
        return None

async def run_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Navigating to Tala job board...")
        await page.goto(JOBS_URL)
        await page.wait_for_selector("a.posting-title")

        job_links = await page.locator("a.posting-title").all()
        job_urls = []

        for link in job_links:
            href = await link.get_attribute("href")
            if href:
                full_url = urljoin(BASE_URL, href)
                job_urls.append(full_url)

        print(f"🔍 Found {len(job_urls)} jobs.")

        jobs = []
        for i, url in enumerate(job_urls, 1):
            print(f"📄 Scraping job {i}/{len(job_urls)}: {url}")
            job_data = await scrape_job_detail(context, url)
            if job_data:
                jobs.append(job_data)

        await browser.close()

        if jobs:
            df = pd.DataFrame(jobs)
            df.to_csv("tala_jobs.csv", index=False, encoding="utf-8")
            print("✅ Saved to tala_jobs.csv")
        else:
            print("⚠️ No jobs scraped successfully.")

if __name__ == "__main__":
    asyncio.run(run_scraper())
