import asyncio
import pandas as pd
from urllib.parse import urljoin
from playwright.async_api import async_playwright

BASE_URL = "https://apply.workable.com"
JOBS_URL = f"{BASE_URL}/deloitte-eastafrica/"

async def scrape_job_detail(context, job_url):
    try:
        page = await context.new_page()
        await page.goto(job_url, timeout=60000)
        await page.wait_for_selector("h1", timeout=20000)

        # Title
        title = await page.locator("h1").text_content()

        # Location
        try:
            location = await page.locator("span.styles--QTMDv.styles--2TdGW").first.text_content()
        except:
            location = "N/A"

        # Category (Department)
        try:
            category = await page.locator('span[data-ui="job-department"]').text_content()
        except:
            category = "N/A"

        # First paragraph of job description
        try:
            desc_el = page.locator('section[data-ui="job-description"] div > p:nth-of-type(1)')
            description = await desc_el.text_content()
        except:
            description = "N/A"

        await page.close()

        return {
            "Job Title": title.strip(),
            "Location": location.strip(),
            "Category": category.strip(),
            "Job Description": description.strip(),
            "Apply Link": job_url
        }
    except Exception as e:
        print(f"❌ Failed to scrape {job_url}: {e}")
        return None

async def run_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Visiting Deloitte East Africa careers page...")
        await page.goto(JOBS_URL)
        await page.wait_for_selector("a.styles--3qpm9", timeout=20000)

        cards = await page.locator("a.styles--3qpm9").all()
        print(f"🔍 Found {len(cards)} job(s).")

        jobs = []
        for idx, card in enumerate(cards, 1):
            href = await card.get_attribute("href")
            if href:
                job_url = urljoin(BASE_URL, href)
                print(f"📄 Scraping job {idx}/{len(cards)}: {job_url}")
                job = await scrape_job_detail(context, job_url)
                if job:
                    jobs.append(job)

        await browser.close()

        if jobs:
            pd.DataFrame(jobs).to_csv("deloitte_jobs.csv", index=False, encoding="utf-8")
            print(f"\n✅ Saved {len(jobs)} jobs to deloitte_jobs.csv")
        else:
            print("⚠️ No jobs scraped.")

if __name__ == "__main__":
    asyncio.run(run_scraper())
