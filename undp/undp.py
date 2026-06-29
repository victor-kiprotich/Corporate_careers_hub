import asyncio
import pandas as pd
from playwright.async_api import async_playwright

BASE_URL = "https://estm.fa.em2.oraclecloud.com"
JOBS_PAGE = (
    f"{BASE_URL}/hcmUI/CandidateExperience/en/sites/CX_1/jobs"
    "?location=Kenya&locationId=300000000440707&locationLevel=country&mode=location"
)

async def scrape_job_detail(page, url):
    try:
        await page.goto(url, timeout=60000)
        await page.wait_for_selector("h1.heading.job-details__title", timeout=20000)

        title = await page.locator("h1.heading.job-details__title").inner_text()
        meta_items = page.locator("ul.job-meta__list li.job-meta__item")
        count = await meta_items.count()

        location = posting_date = vacancy_type = due_date = "N/A"

        for i in range(count):
            try:
                label = await meta_items.nth(i).locator("span.job-meta__title").inner_text()
                value = await meta_items.nth(i).locator("span.job-meta__subitem").inner_text()

                if "Locations" in label:
                    location = value
                elif "Posting Date" in label:
                    posting_date = value
                elif "Vacancy Type" in label:
                    vacancy_type = value
                elif "Apply Before" in label:
                    due_date = value
            except:
                continue

        return {
            "Job Title": title.strip(),
            "Location": location.strip(),
            "Posting Date": posting_date.strip(),
            "Vacancy Type": vacancy_type.strip(),
            "Due Date": due_date.strip(),
            "Apply Link": url
        }

    except Exception as e:
        print(f"❌ Error scraping job detail page {url}: {e}")
        return None

async def run_scraper():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🔗 Opening UNDP Kenya job board...")
        await page.goto(JOBS_PAGE, timeout=60000)

        await page.wait_for_selector("a.job-grid-item__link, a.job-list-item__link", timeout=30000)

        job_links = await page.locator("a.job-grid-item__link, a.job-list-item__link").evaluate_all(
            "els => els.map(el => el.href)"
        )

        print(f"📥 Found {len(job_links)} job links. Scraping each...")

        jobs = []
        for idx, job_url in enumerate(job_links, start=1):
            print(f"🔍 Scraping job {idx}/{len(job_links)}")
            try:
                job_page = await context.new_page()
                job_data = await scrape_job_detail(job_page, job_url)
                if job_data:
                    jobs.append(job_data)
                await job_page.close()
            except Exception as e:
                print(f"⚠️ Failed to scrape {job_url}: {e}")

        await browser.close()

        if jobs:
            df = pd.DataFrame(jobs)
            df.to_csv("undp_kenya_jobs.csv", index=False, encoding="utf-8")
            print(f"✅ {len(jobs)} jobs saved to undp_kenya_jobs.csv")
        else:
            print("⚠️ No jobs scraped.")

if __name__ == "__main__":
    asyncio.run(run_scraper())
