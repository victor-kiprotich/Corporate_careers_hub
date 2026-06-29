import asyncio
import csv
from playwright.async_api import async_playwright

START_URL = "https://kokonetworks.com/careers/"
OUTPUT_FILE = "koko_jobs.csv"

async def extract_job_details(context, url):
    try:
        page = await context.new_page()
        await page.goto(url, timeout=60000)

        await page.wait_for_selector("h2", timeout=10000)

        title = await page.locator("h2").text_content()
        location = await page.locator(".location").text_content()
        job_type = await page.locator(".commitment").text_content()

        # Description block
        desc_locator = "body > div.content-wrapper.posting-page > div > div:nth-child(2) > div:nth-child(1) > div:nth-child(3)"
        await page.wait_for_selector(desc_locator, timeout=10000)
        description = await page.locator(desc_locator).text_content()

        await page.close()

        return {
            "Job Title": title.strip() if title else "N/A",
            "Location": location.strip() if location else "N/A",
            "Type": job_type.strip() if job_type else "N/A",
            "Description": description.strip() if description else "N/A",
            "Apply Link": url
        }

    except Exception as e:
        print(f"⚠️ Failed to scrape job detail page: {url}\nError: {e}")
        return None


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌐 Navigating to KOKO Networks careers...")
        await page.goto(START_URL, timeout=60000)

        # Click the "View open positions" button
        await page.get_by_role("link", name="View open positions").click()

        print("🔍 Waiting for job listings...")
        await page.wait_for_selector("ul.positions-list", timeout=10000)
        job_cards = await page.locator("li").all()

        print(f"📌 Found {len(job_cards)} job card(s). Scraping...")
        results = []

        for i, card in enumerate(job_cards):
            try:
                link = await card.locator("a").get_attribute("href")
                if not link or "lever.co" not in link:
                    continue

                print(f"🔎 [{len(results)+1}] Scraping: {link}")
                job_data = await extract_job_details(context, link)

                if job_data:
                    results.append(job_data)
            except Exception as e:
                print(f"⚠️ Failed to scrape job {i+1}: {e}")

        # Save to CSV
        if results:
            with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["Job Title", "Location", "Type", "Description", "Apply Link"])
                writer.writeheader()
                writer.writerows(results)
            print(f"\n✅ Done! Saved {len(results)} job(s) to {OUTPUT_FILE}")
        else:
            print("❌ No job data extracted.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
