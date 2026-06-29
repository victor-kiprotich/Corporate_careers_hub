import asyncio
import csv
from playwright.async_api import async_playwright

OUTPUT_FILE = "glovo_jobs.csv"

async def scrape_job_detail(context, url):
    try:
        detail_page = await context.new_page()
        await detail_page.goto(url, timeout=60000)

        # Wait for necessary elements
        await detail_page.wait_for_selector("h1.job__title", timeout=10000)
        title = await detail_page.locator("h1.job__title").text_content()
        location = await detail_page.locator("h3.job__extra").text_content()

        # 12th paragraph from the job description
        paragraphs = detail_page.locator("div.job__description p")
        count = await paragraphs.count()

        description = "N/A"
        if count >= 12:
            description = await paragraphs.nth(11).text_content()

        await detail_page.close()

        return {
            "Job Title": title.strip(),
            "Location": location.strip(),
            "Description": description.strip()
        }

    except Exception as e:
        print(f"⚠️ Error scraping job detail from {url}: {e}")
        return {
            "Job Title": "N/A",
            "Location": "N/A",
            "Description": "N/A"
        }

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌐 Visiting Glovo Kenya jobs page...")
        await page.goto("https://jobs.glovoapp.com/find-your-ride/?l=kenya", timeout=60000)

        await page.wait_for_selector("a.b__jobs_item", timeout=15000)
        job_cards = page.locator("a.b__jobs_item")
        count = await job_cards.count()
        print(f"🔍 Found {count} job(s).")

        results = []

        for i in range(count):
            try:
                card = job_cards.nth(i)
                href = await card.get_attribute("href")
                full_url = href if href.startswith("http") else f"https://jobs.glovoapp.com{href}"

                print(f"🔎 Scraping job {i+1}: {full_url}")
                details = await scrape_job_detail(context, full_url)
                details["Apply Link"] = full_url

                results.append(details)
            except Exception as e:
                print(f"⚠️ Failed to process job {i+1}: {e}")

        # Save to CSV
        with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Job Title", "Location", "Description", "Apply Link"])
            writer.writeheader()
            writer.writerows(results)

        print(f"\n✅ Saved {len(results)} job(s) to {OUTPUT_FILE}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
