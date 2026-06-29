import asyncio
import csv
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = "https://ke.ncbagroup.com/job-openings/"
CSV_FILE = "ncba_jobs.csv"


def parse_date(text: str) -> str:
    text = text.strip()
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return text


async def scrape_ncba_jobs():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Navigating to NCBA Careers page...")
        try:
            await page.goto(BASE_URL, timeout=60000)
            await page.wait_for_selector("h2.entry-title a", timeout=30000)
        except PlaywrightTimeoutError:
            print("❌ Jobs list did not load. Check selector or site availability.")
            await browser.close()
            return

        # Grab job links
        job_elements = await page.locator("h2.entry-title a").all()
        total_jobs = len(job_elements)
        print(f"✅ Found {total_jobs} job listing(s).")

        results = []

        for i, job in enumerate(job_elements):
            try:
                title = (await job.inner_text()).strip()
                link = await job.get_attribute("href")

                detail_page = await context.new_page()
                try:
                    await detail_page.goto(link, timeout=30000)
                    await detail_page.wait_for_selector(".awsm-job-wrapper", timeout=15000)

                    async def safe_text(selector):
                        loc = detail_page.locator(selector)
                        return (await loc.inner_text()).strip() if await loc.count() else ""

                    department = await safe_text(".awsm-job-specification-item:has-text('Division/Department:') .awsm-job-specification-term")
                    positions = await safe_text(".awsm-job-specification-item:has-text('Positions:') .awsm-job-specification-term")
                    closing_date_raw = await safe_text(".awsm-job-expiration-content")
                    closing_date = parse_date(closing_date_raw)

                    results.append({
                        "Title": title,
                        "Location": "Nairobi",
                        "Link": link,
                        "Department": department,
                        "Positions": positions,
                        "Closing Date": closing_date,
                    })

                    print(f"✅ {title} | Dept: {department} | Closing: {closing_date}")
                finally:
                    await detail_page.close()

            except Exception as e:
                print(f"❌ Error scraping job {i+1}: {e}")

        # Save results
        with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Link", "Department", "Positions", "Closing Date"])
            writer.writeheader()
            writer.writerows(results)

        print(f"\n💾 Saved {len(results)} jobs to {CSV_FILE}.")
        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(scrape_ncba_jobs())
