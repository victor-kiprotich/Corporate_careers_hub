import asyncio
import csv
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

async def scrape_rentokil_jobs():
    base_url = "https://www.rentokil.co.ke"
    jobs_url = f"{base_url}/careers/"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Navigating to Rentokil Kenya Careers page...")
        try:
            await page.goto(jobs_url, timeout=60000, wait_until="domcontentloaded")
        except PlaywrightTimeoutError:
            print("❌ Timeout loading careers page.")
            await browser.close()
            return

        await page.wait_for_timeout(5000)  # allow dynamic content to load

        # Select all job cards (adjust selector to match site structure)
        job_cards = await page.locator("a.careers-job-card").all()
        print(f"✅ Found {len(job_cards)} job cards")

        results = []

        for idx, card in enumerate(job_cards):
            try:
                job_title = await card.locator("h3.job-title").inner_text()
                location = await card.locator("span.job-location").inner_text()
                if "Kenya" not in location:
                    continue  # skip non-Kenya roles

                href = await card.get_attribute("href")
                full_link = f"{base_url}{href}" if href.startswith("/") else href

                detail_page = await context.new_page()
                await detail_page.goto(full_link, timeout=60000)
                await detail_page.wait_for_timeout(3000)

                # Extract description (adjust as needed)
                description = await detail_page.locator("div.job-description").inner_text()

                results.append({
                    "Title": job_title.strip(),
                    "Location": location.strip(),
                    "Description": description.strip(),
                    "Link": full_link.strip()
                })

                print(f"✅ Scraped: {job_title.strip()} ({location.strip()})")
                await detail_page.close()

            except Exception as e:
                print(f"⚠️ Skipped job {idx+1}: {e}")
                continue

        await browser.close()

    # Save to CSV
    if results:
        with open("rentokil_kenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Description", "Link"])
            writer.writeheader()
            writer.writerows(results)
        print(f"\n✅ Saved {len(results)} Kenya-based jobs to rentokil_kenya_jobs.csv")
    else:
        print("\n❌ No Kenya-based jobs found.")

if __name__ == "__main__":
    asyncio.run(scrape_rentokil_jobs())
