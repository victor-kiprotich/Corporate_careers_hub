import asyncio
import csv
from playwright.async_api import async_playwright


async def scrape_iwg_jobs():
    url = "https://jobs.iwgplc.com/jobs/search?query=kenya"
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Set to False for debugging
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Navigating to IWG Kenya job board...")
        await page.goto(url, timeout=60000)

        # Close popup modal if it appears
        try:
            close_btn = await page.wait_for_selector('button:has-text("Close")', timeout=5000)
            await close_btn.click()
        except:
            pass

        # Wait for job cards
        await page.wait_for_selector("div.job-search-results-card", timeout=20000)
        job_cards = await page.query_selector_all("div.job-search-results-card")

        print(f"📦 Found {len(job_cards)} job(s)")

        for i, card in enumerate(job_cards):
            try:
                # Title
                title_el = await card.query_selector("h3.card-title a")
                title = await title_el.inner_text() if title_el else "N/A"
                link = await title_el.get_attribute("href") if title_el else ""

                # Full link
                job_link = link if link.startswith("http") else f"https://jobs.iwgplc.com{link}"

                # Location
                location_el = await card.query_selector("span[id^='location']")
                location = await location_el.inner_text() if location_el else "N/A"

                # Employment Type
                type_el = await card.query_selector("span[id^='employment_type']")
                emp_type = await type_el.inner_text() if type_el else "N/A"

                # Summary
                summary_el = await card.query_selector("p.card-text")
                summary = await summary_el.inner_text() if summary_el else "N/A"

                results.append({
                    "Title": title.strip(),
                    "Location": location.strip(),
                    "Employment Type": emp_type.strip(),
                    "Summary": summary.strip(),
                    "Link": job_link.strip()
                })

                print(f"[{i+1}] ✅ {title.strip()} - {location.strip()}")

            except Exception as e:
                print(f"[{i+1}] ❌ Error: {e}")

        await browser.close()

    # Save to CSV
    keys = ["Title", "Location", "Employment Type", "Summary", "Link"]
    with open("iwg_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Saved {len(results)} job(s) to iwg_jobs.csv")


if __name__ == "__main__":
    asyncio.run(scrape_iwg_jobs())

