import asyncio
import csv
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


async def scrape_prospect33_jobs():
    start_url = "https://prospect33.com/careers/"

    print("🌍 Navigating to Prospect33 Careers page...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(start_url, timeout=90000, wait_until="domcontentloaded")
        except PlaywrightTimeoutError:
            print("❌ Error: Page load timed out. Trying again with networkidle strategy...")
            try:
                await page.goto(start_url, timeout=120000, wait_until="networkidle")
            except PlaywrightTimeoutError:
                print("❌ Failed to load the careers page after retries.")
                await browser.close()
                return

        await page.wait_for_timeout(5000)  # allow JS rendering

        job_cards = await page.locator("a.normal").all()
        print(f"✅ Found {len(job_cards)} job cards")

        jobs = []

        for idx, card in enumerate(job_cards):
            try:
                job_link = await card.get_attribute("href")
                job_title = await card.inner_text()
                full_link = f"https://prospect33.com{job_link}" if job_link.startswith("/") else job_link

                print(f"🔗 Visiting: {full_link}")
                detail_page = await context.new_page()
                await detail_page.goto(full_link, timeout=60000)

                # Title
                title = await detail_page.locator("h1").inner_text()

                # Location
                location_elem = detail_page.locator("b", has_text="Primary Location:")
                location = await location_elem.evaluate("el => el.nextSibling.textContent") if await location_elem.count() > 0 else "N/A"
                location = location.strip() if location else "N/A"

                # Description
                description_elem = detail_page.locator("div.et_pb_text_inner p").first
                description = await description_elem.inner_text() if await description_elem.count() > 0 else "N/A"

                # Apply Link (same as job link)
                apply_link = full_link

                jobs.append({
                    "Title": title,
                    "Location": location,
                    "Description": description,
                    "Link": full_link,
                    "Apply Link": apply_link
                })

                await detail_page.close()

            except Exception as e:
                print(f"⚠️ Skipped job {idx + 1}: {e}")
                continue

        # Save to CSV
        if jobs:
            keys = jobs[0].keys()
            with open("prospect33_jobs.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(jobs)
            print(f"✅ Saved {len(jobs)} jobs to prospect33_jobs.csv")
        else:
            print("❌ No jobs found or all failed to load.")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(scrape_prospect33_jobs())
