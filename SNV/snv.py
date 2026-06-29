import asyncio
import csv
from playwright.async_api import async_playwright

BASE_URL = "https://www.snv.org"
START_URL = f"{BASE_URL}/careers?country=kenya"
OUTPUT_FILE = "snv_kenya_jobs.csv"

async def extract_job_details(context, url):
    try:
        page = await context.new_page()
        await page.goto(url, timeout=60000)

        # Extract title
        title_el = page.locator("h1")
        await title_el.wait_for(timeout=10000)
        title = (await title_el.text_content()).strip()

        await page.close()
        return {
            "Job Title": title,
            "Location": "Kenya",
            "Apply Link": url
        }
    except Exception as e:
        print(f"⚠️ Failed to extract job detail from {url}: {e}")
        return None

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌐 Opening SNV Kenya careers page...")
        await page.goto(START_URL, timeout=60000)

        # Wait for the main container
        await page.wait_for_selector("div.col-span-12.lg\\:col-span-8", timeout=10000)

        # Check if "No results found" exists
        no_results = await page.locator("text=No results found").count()
        if no_results > 0:
            print("❌ No jobs currently posted for Kenya.")
            await browser.close()
            return

        # Otherwise, collect job cards
        job_links = await page.locator("div.col-span-12.lg\\:col-span-8 a").all()
        print(f"🔍 Found {len(job_links)} job(s)")

        results = []
        for i, job_link in enumerate(job_links):
            href = await job_link.get_attribute("href")
            if not href:
                continue

            full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
            print(f"🔎 [{i+1}] {full_url}")
            job_data = await extract_job_details(context, full_url)
            if job_data:
                results.append(job_data)

        # Save to CSV
        if results:
            with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["Job Title", "Location", "Apply Link"])
                writer.writeheader()
                writer.writerows(results)

            print(f"\n✅ Done! Saved {len(results)} job(s) to {OUTPUT_FILE}")
        else:
            print("⚠️ No job data to save.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
