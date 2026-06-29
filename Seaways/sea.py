import asyncio
import csv
from playwright.async_api import async_playwright

async def scrape_seaways_jobs():
    base_url = "https://seaways.net"
    jobs_url = f"{base_url}/jobs/?job__location_spec=nairobi"
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Navigating to Seaways Nairobi jobs...")
        await page.goto(jobs_url, timeout=60000)
        await page.wait_for_selector("div.awsm-job-listing-item")

        job_cards = await page.locator("div.awsm-job-listing-item a").all()

        print(f"✅ Found {len(job_cards)} job(s)")

        for i, job_card in enumerate(job_cards, start=1):
            try:
                title = await job_card.inner_text()
                link = await job_card.get_attribute("href")
                full_link = link if link.startswith("http") else f"{base_url}{link}"

                # Open job detail page
                detail_page = await context.new_page()
                await detail_page.goto(full_link, timeout=60000)
                await detail_page.wait_for_selector("div.awsm-job-specification-item")

                # Extract location
                location = await detail_page.locator(
                    "div.awsm-job-specification-job-location span.awsm-job-specification-term"
                ).inner_text()

                # Extract job type
                job_type = await detail_page.locator(
                    "div.awsm-job-specification-job-type span.awsm-job-specification-term"
                ).inner_text()

                print(f"[{i}] Scraped: {title} | {location} | {job_type}")

                results.append({
                    "Title": title.strip(),
                    "Location": location.strip(),
                    "Job Type": job_type.strip(),
                    "Link": full_link.strip()
                })

                await detail_page.close()

            except Exception as e:
                print(f"⚠️ Skipped job {i} due to error: {e}")
                continue

        await browser.close()

    # Save to CSV
    with open("seaways_nairobi_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Job Type", "Link"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Saved {len(results)} job(s) to seaways_nairobi_jobs.csv")


# Run the scraper
if __name__ == "__main__":
    asyncio.run(scrape_seaways_jobs())

