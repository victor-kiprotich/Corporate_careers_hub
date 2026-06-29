import asyncio
import csv
from playwright.async_api import async_playwright

BASE_URL = "https://careers.midisgroup.com"
START_URL = f"{BASE_URL}/search/?createNewAlert=false&q=&locationsearch=&optionsFacetsDD_country=KE"

OUTPUT_FILE = "midis_kenya_jobs.csv"

async def extract_job_details(context, url):
    try:
        page = await context.new_page()
        await page.goto(url, timeout=60000)

        title = await page.locator('[data-careersite-propertyid="title"]').text_content()
        location = await page.locator(".jobGeoLocation").text_content()
        posting_date = await page.locator('[data-careersite-propertyid="date"]').text_content()

        # Wait for description section
        await page.wait_for_selector("#content p", timeout=10000)
        paragraphs = await page.locator("#content p").all()
        description = await paragraphs[0].text_content() if paragraphs else "N/A"

        await page.close()

        return {
            "Job Title": title.strip(),
            "Location": location.strip(),
            "Posting Date": posting_date.strip(),
            "Description": description.strip(),
            "Apply Link": url
        }

    except Exception as e:
        print(f"❌ Failed to extract job detail from {url}: {e}")
        return None

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Navigating to Midis Group Kenya jobs...")
        await page.goto(START_URL, timeout=60000)
        await page.wait_for_selector("a.jobTitle-link", timeout=15000)

        job_cards = await page.locator("a.jobTitle-link").all()
        print(f"📌 Found {len(job_cards)} job(s). Scraping...")

        results = []
        seen_urls = set()

        for i, card in enumerate(job_cards):
            try:
                href = await card.get_attribute("href")
                full_url = f"{BASE_URL}{href}"
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                print(f"🔎 [{len(results)+1}] Scraping: {full_url}")
                job_data = await extract_job_details(context, full_url)
                if job_data:
                    results.append(job_data)

            except Exception as e:
                print(f"⚠️ Skipped job {i+1} due to error: {e}")

        if results:
            with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "Job Title", "Location", "Posting Date", "Description", "Apply Link"
                ])
                writer.writeheader()
                writer.writerows(results)

            print(f"\n✅ Done! Saved {len(results)} job(s) to {OUTPUT_FILE}")
        else:
            print("❌ No job data extracted.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
