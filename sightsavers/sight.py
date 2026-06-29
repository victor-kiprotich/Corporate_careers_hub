import asyncio
import csv
from urllib.parse import urljoin
from playwright.async_api import async_playwright, TimeoutError

async def scrape_sightsavers_kenya_jobs():
    base_url = "https://careers.sightsavers.org"
    job_listing_url = f"{base_url}/jobs?location=Kenya&woe=12&regionCode=KE&stretchUnit=MILES&stretch=10&page=1"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Navigating to Sightsavers Kenya job listings...")
        await page.goto(job_listing_url, timeout=60000)

        await page.wait_for_selector("a.job-title-link", timeout=15000)
        job_cards = await page.locator("a.job-title-link").all()

        if not job_cards:
            print("❌ No jobs found.")
            await browser.close()
            return

        print(f"✅ Found {len(job_cards)} job(s).\n")
        jobs = []

        for i, job in enumerate(job_cards):
            try:
                href = await job.get_attribute("href")
                title = (await job.inner_text()).strip()
                full_url = urljoin(base_url, href)

                detail_page = await context.new_page()
                await detail_page.goto(full_url, timeout=30000)
                await detail_page.wait_for_selector("span.job-data-span", timeout=10000)

                location = await detail_page.locator("span.job-data-span").nth(0).inner_text()
                category = await detail_page.locator("li#header-categories span.job-data-span").inner_text()
                due_date = await detail_page.locator("li#header-tags9 span.job-data-span").inner_text()
                description = await detail_page.locator("p").first.inner_text()

                print(f"📄 {title} | {location}")

                jobs.append({
                    "title": title,
                    "location": location.strip(),
                    "category": category.strip(),
                    "due_date": due_date.strip(),
                    "description": description.strip(),
                    "link": full_url
                })

                await detail_page.close()

            except Exception as e:
                print(f"⚠️ Error scraping job {i + 1}: {e}")

        # Save to CSV
        with open("sightsavers_kenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "location", "category", "due_date", "description", "link"])
            writer.writeheader()
            writer.writerows(jobs)

        print(f"\n✅ Saved {len(jobs)} job(s) to sightsavers_kenya_jobs.csv")

        await context.close()
        await browser.close()

# Run the async scraper
asyncio.run(scrape_sightsavers_kenya_jobs())
