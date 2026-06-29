import asyncio
import pandas as pd
from playwright.async_api import async_playwright

BASE_URL = "https://eoin.fa.em3.oraclecloud.com"
JOBS_URL = f"{BASE_URL}/hcmUI/CandidateExperience/en/sites/CX_3001/jobs?location=Kenya&locationId=300000000385420&locationLevel=country&mode=job-location"

async def scrape_job_detail(page, url):
    await page.goto(url, timeout=60000)
    await page.wait_for_selector("h1.heading.job-details__title", timeout=20000)

    # Job title
    job_title = await page.locator("h1.heading.job-details__title").text_content()


    # Metadata block
    location =  posting_date = "N/A"
    items = page.locator("ul.job-meta__list li.job-meta__item")

    for i in range(await items.count()):
        key = await items.nth(i).locator("span.job-meta__title").text_content()
        val = await items.nth(i).locator("span.job-meta__subitem").text_content()
        if "Location" in key:
            location = val.strip()
        elif "Posting Date" in key:
            posting_date = val.strip()

    return {
        "Job Title": job_title.strip(),
        "Location": location,
        "Posting Date": posting_date,
        "Apply Link": url
    }

async def run_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌐 Navigating to KCB job board...")
        await page.goto(JOBS_URL, timeout=60000)
        await page.wait_for_selector("a.job-list-item__link", timeout=30000)

        # Get all job detail page URLs
        job_elements = await page.locator("a.job-list-item__link").all()
        job_urls = []
        for el in job_elements:
            href = await el.get_attribute("href")
            if href:
                full_url = href if href.startswith("http") else BASE_URL + href
                job_urls.append(full_url)

        print(f"📌 Found {len(job_urls)} jobs to scrape.")

        jobs = []
        for i, job_url in enumerate(job_urls, 1):
            print(f"🔍 Scraping job {i}/{len(job_urls)}: {job_url}")
            try:
                job_page = await context.new_page()
                job_data = await scrape_job_detail(job_page, job_url)
                jobs.append(job_data)
                await job_page.close()
            except Exception as e:
                print(f"❌ Error scraping {job_url}: {e}")

        await browser.close()

        if jobs:
            pd.DataFrame(jobs).to_csv("kcb_jobs.csv", index=False, encoding="utf-8")
            print("✅ Saved {len(jobs)} jobs to kcb_jobs.csv")
        else:
            print("⚠️ No job data extracted.")

if __name__ == "__main__":
    asyncio.run(run_scraper())
