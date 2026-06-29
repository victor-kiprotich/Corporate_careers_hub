import asyncio
import csv
from urllib.parse import urljoin
from playwright.async_api import async_playwright

BASE_URL = "https://www.mckinsey.com/careers/search-jobs?cities=Nairobi"


async def scrape_mckinsey_jobs():
    jobs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Navigating to McKinsey Nairobi job listings...")
        await page.goto(BASE_URL, timeout=60000)
        await page.wait_for_load_state("networkidle")

        # Wait for job cards
        await page.wait_for_selector("li.job-listing", timeout=20000)
        job_cards = await page.locator("li.job-listing").all()
        print(f"📦 Found {len(job_cards)} job(s)\n")

        for i, card in enumerate(job_cards):
            try:
                # Job title & link
                title_link_el = card.locator("h2.headline a")
                title = (await title_link_el.inner_text()).strip()
                href = await title_link_el.get_attribute("href")
                full_link = urljoin(BASE_URL, href) if href else "N/A"

                # Department
                dept_el = card.locator("p.interests span:not(.visually-hidden) + span")
                department = (await dept_el.inner_text()).strip() if await dept_el.count() else ""

                # Locations
                location_els = await card.locator("li.city").all()
                location_list = [await loc.inner_text() for loc in location_els]
                location_text = ", ".join(location_list)

                jobs.append({
                    "title": title,
                    "location": location_text,
                    "department": department,
                    "link": full_link
                })

                print(f"✅ {title}")

            except Exception as e:
                print(f"❌ Error scraping job {i + 1}: {e}")

        # Save to CSV
        with open("mckinsey_nairobi_jobs.csv", "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "location", "department", "link"])
            writer.writeheader()
            writer.writerows(jobs)

        print(f"\n💾 Saved {len(jobs)} jobs to mckinsey_nairobi_jobs.csv")

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(scrape_mckinsey_jobs())
