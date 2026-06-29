import asyncio
import csv
from playwright.async_api import async_playwright

OUTPUT_CSV = "qona_jobs.csv"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌐 Visiting Qona Sacco Careers page...")
        await page.goto("https://qonasacco.com/careers/", timeout=60000)
        await page.wait_for_selector("a[href*='?post_type=job_listing']", timeout=20000)

        job_anchors = page.locator("a[href*='?post_type=job_listing']")
        count = await job_anchors.count()

        print(f"📌 Found {count} job(s). Scraping...")

        job_data = []

        for i in range(count):
            anchor = job_anchors.nth(i)
            try:
                link = await anchor.get_attribute("href")
                title = await anchor.locator("h3").inner_text()
                location = await anchor.locator("div.location").inner_text()
                job_type = await anchor.locator("li.job-type").inner_text()
                date_posted = await anchor.locator("li.date time").get_attribute("datetime")

                job_data.append({
                    "title": title.strip(),
                    "url": link.strip(),
                    "location": location.strip(),
                    "job_type": job_type.strip(),
                    "date_posted": date_posted.strip()
                })
            except Exception as e:
                print(f"⚠️ Failed to extract job {i + 1}: {e}")

        # Save to CSV
        if job_data:
            with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["title", "url", "location", "job_type", "date_posted"])
                writer.writeheader()
                writer.writerows(job_data)
            print(f"✅ Done! Saved {len(job_data)} job(s) to {OUTPUT_CSV}")
        else:
            print("❌ No job data collected.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
