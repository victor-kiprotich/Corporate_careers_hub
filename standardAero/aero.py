import asyncio
import pandas as pd
from playwright.async_api import async_playwright

BASE_URL = "https://cva.fa.us1.oraclecloud.com"
JOBS_URL = f"{BASE_URL}/hcmUI/CandidateExperience/en/sites/CX_3/jobs?location=Kenya&locationId=300000000193969&locationLevel=country&mode=location"

async def scrape_job_detail(page, url):
    try:
        await page.goto(url, timeout=60000)
        await page.wait_for_selector("h1.heading.job-details__title", timeout=20000)

        job_title = await page.locator("h1.heading.job-details__title").text_content()
        # Parse metadata
        meta_items = page.locator("ul.job-meta__list li.job-meta__item")
        count = await meta_items.count()

        category = location = posting_date = "N/A"
        for i in range(count):
            try:
                title = await meta_items.nth(i).locator("span.job-meta__title").text_content()
                value = await meta_items.nth(i).locator("span.job-meta__subitem").text_content()
                if "Job Category" in title:
                    category = value
                elif "Posting Date" in title:
                    posting_date = value
                elif "Locations" in title:
                    location = value
            except:
                continue

        return {
            "Job Title": job_title.strip() if job_title else "N/A",
            "Location": location.strip(),
            "Category": category.strip(),
            "Posting Date": posting_date.strip(),
            "Apply Link": url
        }

    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return None

async def run_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌐 Navigating to job board...")
        await page.goto(JOBS_URL, timeout=60000)
        await page.wait_for_selector("a.job-grid-item__link", timeout=20000)

        job_elements = await page.locator("a.job-grid-item__link").all()
        job_urls = []

        for el in job_elements:
            href = await el.get_attribute("href")
            if href:
                full_url = href if href.startswith("http") else BASE_URL + href
                job_urls.append(full_url)

        print(f"🔍 Found {len(job_urls)} jobs.")

        jobs = []
        for i, job_url in enumerate(job_urls, 1):
            print(f"📄 Scraping job {i}/{len(job_urls)}: {job_url}")
            job_page = await context.new_page()
            job_data = await scrape_job_detail(job_page, job_url)
            if job_data:
                jobs.append(job_data)
            await job_page.close()

        await browser.close()

        if jobs:
            df = pd.DataFrame(jobs)
            df.to_csv("aero.csv", index=False, encoding="utf-8")
            print("✅ Saved to aero.csv")
        else:
            print("⚠️ No jobs scraped successfully.")

if __name__ == "__main__":
    asyncio.run(run_scraper())
