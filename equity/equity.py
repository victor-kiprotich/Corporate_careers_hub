import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import pandas as pd

EQUITY_JOB_BOARD = "https://equitybank.taleo.net/careersection/ext_new/jobsearch.ftl?lang=en"

async def run_equity_scraper(playwright):
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()

    print("🔗 Opening Equity Bank job board...")
    await page.goto(EQUITY_JOB_BOARD)
    await page.wait_for_selector("tbody.jobsbody", timeout=15000)

    print("📥 Extracting job postings from table...")
    html = await page.inner_html("tbody.jobsbody")
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("tr")

    job_data = []
    for row in rows:
        title_tag = row.find("th").find("a")
        job_title = title_tag.text.strip() if title_tag else "N/A"
        job_detail_link = "https://equitybank.taleo.net" + title_tag.get("href") if title_tag else EQUITY_JOB_BOARD

        cells = row.find_all("td")
        job_location = cells[1].text.strip() if len(cells) > 1 else "N/A"
        posting_date = cells[2].text.strip() if len(cells) > 2 else "N/A"

        job_data.append({
            "Job Title": job_title,
            "Location": job_location,
            "Organization Name": "Equity Bank",
            "Posting Date": posting_date,
            "Apply Link": job_detail_link  # ✅ Now linking to job detail page
        })

    df = pd.DataFrame(job_data)
    df.to_csv("equity_bank_jobs.csv", index=False, encoding="utf-8")
    print(f"✅ Extracted {len(job_data)} jobs. Saved to 'equity_bank_jobs_async.csv'.")

    await browser.close()

async def main():
    async with async_playwright() as playwright:
        await run_equity_scraper(playwright)

if __name__ == "__main__":
    asyncio.run(main())
