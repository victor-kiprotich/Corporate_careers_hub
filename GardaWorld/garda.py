import asyncio
import csv
from playwright.async_api import async_playwright

BASE_URL = "https://jobs.garda.com"
OUTPUT_FILE = "garda_jobs_kenya.csv"

async def scrape_garda_jobs():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Set headless=False to see browser
        context = await browser.new_context()
        page = await context.new_page()

        print("🌐 Opening Garda Kenya job listings...")
        await page.goto(
            f"{BASE_URL}/search/?createNewAlert=false&q=&locationsearch=kenya&optionsFacetsDD_dept=",
            timeout=60000
        )

        await page.wait_for_selector("a.jobTitle-link", timeout=15000)
        job_links = await page.locator("a.jobTitle-link").all()

        print(f"🔍 Found {len(job_links)} jobs.")

        results = []

        for i, link in enumerate(job_links):
            try:
                relative_href = await link.get_attribute("href")
                full_url = BASE_URL + relative_href
                job_page = await context.new_page()
                await job_page.goto(full_url, timeout=60000)

                # Extract details
                title = await job_page.locator("span[itemprop='title']").text_content() or "N/A"
                location = await job_page.locator("span.jobGeoLocation").text_content() or "N/A"
                category = await job_page.locator("span[itemprop='industry']").text_content() or "N/A"

                print(f"✅ [{i+1}] {title.strip()}")

                results.append({
                    "Job Title": title.strip(),
                    "Location": location.strip(),
                    "Category": category.strip(),
                    "Apply Link": full_url
                })

                await job_page.close()

            except Exception as e:
                print(f"⚠️ Skipped a job due to error: {e}")

        # Save to CSV
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Job Title", "Location", "Category", "Apply Link"])
            writer.writeheader()
            writer.writerows(results)

        print(f"\n✅ Saved {len(results)} jobs to {OUTPUT_FILE}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_garda_jobs())
