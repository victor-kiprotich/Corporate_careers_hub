import asyncio
import csv
from playwright.async_api import async_playwright, TimeoutError

async def scrape_ntt_kenya_jobs():
    base_url = "https://careers.services.global.ntt"
    jobs_url = f"{base_url}/global/en/search-results"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Navigating to NTT global careers...")
        try:
            await page.goto(jobs_url, timeout=60000, wait_until="domcontentloaded")
        except TimeoutError:
            print("❌ Timeout while loading page.")
            await browser.close()
            return

        # Try to close overlay if it exists
        try:
            overlay = page.locator("div.truste_overlay")
            if await overlay.is_visible():
                await page.evaluate("""() => {
                    document.querySelectorAll('.truste_overlay, #truste-consent-button, .truste_popframe').forEach(el => el.remove());
                }""")
                print("✅ Dismissed overlay")
        except Exception:
            print("⚠️ No overlay to dismiss")

        # Open the Country filter
        try:
            await page.wait_for_selector('button:has-text("Country")', timeout=15000)
            await page.click('button:has-text("Country")')
            await page.wait_for_selector('label:has-text("Kenya")', timeout=10000)
            await page.click('label:has-text("Kenya")')
            await page.wait_for_timeout(5000)
        except TimeoutError:
            print("❌ Could not apply country filter")
            await browser.close()
            return

        # Get jobs
        job_cards = page.locator("li.jobs-list-item")
        count = await job_cards.count()
        print(f"📦 Found {count} job(s)")

        if count == 0:
            print("🚫 No jobs available.")
            await browser.close()
            return

        results = []

        for i in range(count):
            try:
                job = job_cards.nth(i)

                location = await job.locator("span.job-location").inner_text()
                if "Kenya" not in location:
                    continue

                title = await job.locator("span.au-target").first.inner_text()
                link = await job.locator("a.apply-btn").get_attribute("href")
                full_link = link if link.startswith("http") else f"{base_url}{link}"
                description = await job.locator("p.job-description").inner_text()

                results.append({
                    "Title": title.strip(),
                    "Location": location.strip(),
                    "Description": description.strip(),
                    "Link": full_link.strip()
                })
                print(f"✅ Scraped: {title.strip()}")

            except Exception as e:
                print(f"⚠️ Skipped job {i+1}: {e}")

        await browser.close()

    if results:
        with open("ntt_kenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Description", "Link"])
            writer.writeheader()
            writer.writerows(results)
        print(f"\n✅ Saved {len(results)} Kenya jobs to 'ntt_kenya_jobs.csv'")
    else:
        print("\n🚫 No Kenya jobs scraped.")

if __name__ == "__main__":
    asyncio.run(scrape_ntt_kenya_jobs())
