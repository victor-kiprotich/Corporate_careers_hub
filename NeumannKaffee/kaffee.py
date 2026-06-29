import asyncio
import csv
from playwright.async_api import async_playwright

async def scrape_nkg_jobs():
    base_url = "https://nkg.wd103.myworkdayjobs.com"
    jobs_url = base_url + "/en-US/nkg?locationCountry=9e684fd7be1e469d9ee955a4c3b754be"

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Navigating to NKG job board...")
        await page.goto(jobs_url, timeout=60000)

        await page.wait_for_selector("a.css-19uc56f", timeout=30000)
        job_cards = await page.query_selector_all("a.css-19uc56f")

        print(f"📦 Found {len(job_cards)} job(s)")

        for i, card in enumerate(job_cards):
            title_el = await card.query_selector("h2")
            job_title = await title_el.inner_text() if title_el else "N/A"

            job_link = await card.get_attribute("href")
            full_link = base_url + job_link if job_link else ""

            detail_page = await context.new_page()
            await detail_page.goto(full_link, timeout=30000)

            try:
                await detail_page.wait_for_selector("h2[data-automation-id='jobPostingHeader']", timeout=15000)

                # Title (confirm again from detail)
                header = await detail_page.query_selector("h2[data-automation-id='jobPostingHeader']")
                job_title = await header.inner_text() if header else job_title

                # Location
                location_el = await detail_page.query_selector("div[data-automation-id='locations'] dd")
                location = await location_el.inner_text() if location_el else "N/A"

                # Date posted (optional)
                try:
                    date_posted_el = await detail_page.query_selector("div[data-automation-id='postedOn'] dd")
                    date_posted = await date_posted_el.inner_text() if date_posted_el else ""
                except:
                    date_posted = ""

                # Description (first paragraph or short text)
                try:
                    desc_el = await detail_page.query_selector("div[data-automation-id='jobDescription']")
                    description = await desc_el.inner_text() if desc_el else ""
                    description = description[:300] + "..." if len(description) > 300 else description
                except:
                    description = ""

                results.append({
                    "Title": job_title.strip(),
                    "Location": location.strip(),
                    "Date Posted": date_posted.strip(),
                    "Description": description.strip(),
                    "Link": full_link.strip()
                })

                print(f"[{i+1}] ✅ {job_title.strip()} - {location.strip()}")

            except Exception as e:
                print(f"[{i+1}] ❌ Error: {e}")

            await detail_page.close()

        await browser.close()

    # Save to CSV
    keys = ["Title", "Location", "Date Posted", "Description", "Link"]
    with open("nkg_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)

    print(f"✅ Saved {len(results)} job(s) to nkg_jobs.csv")


if __name__ == "__main__":
    asyncio.run(scrape_nkg_jobs())
