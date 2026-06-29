import asyncio
import csv
import re
from playwright.async_api import async_playwright

OUTPUT_FILE = "kpc_jobs.csv"
URL = "https://kpc.co.ke/career/"

async def scrape_kpc_jobs():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Set headless=False to watch
        context = await browser.new_context()
        page = await context.new_page()

        print("🌐 Visiting KPC Careers Page...")
        await page.goto(URL, timeout=60000)

        # Click "Current Vacancies" tab
        await page.locator("#wpr-tab-2181").click()
        await page.wait_for_timeout(3000)

        job_sections = page.locator("div.wpr-accordion-item")
        count = await job_sections.count()
        print(f"📄 Found {count} job postings.")

        jobs = []

        for i in range(count):
            try:
                job = job_sections.nth(i)

                title = await job.locator("div.wpr-accordion-header").inner_text()
                content = await job.locator("div.wpr-accordion-content").inner_text()

                # Extract closing date from the content
                match = re.search(r"Closing Date[:\-]?\s*(.+)", content, re.IGNORECASE)
                closing_date = match.group(1).strip() if match else "N/A"

                jobs.append({
                    "Job Title": title.strip(),
                    "Closing Date": closing_date,
                    "Details": content.strip()
                })

                print(f"✅ {title.strip()} — Closing: {closing_date}")

            except Exception as e:
                print(f"⚠️ Skipped a job due to error: {e}")

        # Save to CSV
        with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Job Title", "Closing Date", "Details"])
            writer.writeheader()
            writer.writerows(jobs)

        print(f"\n📁 Saved {len(jobs)} jobs to {OUTPUT_FILE}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_kpc_jobs())
