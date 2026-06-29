import asyncio
from playwright.async_api import async_playwright
import csv

async def scrape_accor_jobs():
    base_url = "https://careers.accor.com"
    jobs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Set to False for debugging
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Navigating to Accor Kenya jobs...")
        await page.goto("https://careers.accor.com/global/en/jobs?q=&options=&page=1&ln=Kenya&lr=1&li=KE", timeout=60000)

        # Wait for job cards
        await page.wait_for_selector("a.attrax-vacancy-tile__title")

        job_links = await page.locator("a.attrax-vacancy-tile__title").all()
        print(f"✅ Found {len(job_links)} job(s)")

        for i, job_card in enumerate(job_links):
            try:
                link = await job_card.get_attribute("href")
                full_link = f"{base_url}{link}" if link.startswith("/") else link

                detail_page = await context.new_page()
                await detail_page.goto(full_link, timeout=60000)

                # Title
                await detail_page.wait_for_selector("span#headertext", timeout=15000)
                title = await detail_page.locator("span#headertext").inner_text()

                # Location (from detail page)
                try:
                    location = await detail_page.locator("li.JobLocation-wrapper").inner_text()
                except:
                    location = "N/A"

                # Category
                try:
                    category = await detail_page.locator("li.JobCategory-wrapper").inner_text()
                except:
                    category = "N/A"

                # Description (first meaningful paragraph)
                try:
                    desc_el = await detail_page.locator("div[class*='jobdescription'] p").first
                    description = await desc_el.inner_text()
                except:
                    description = "N/A"

                print(f"📄 [{i+1}] {title.strip()}")

                jobs.append({
                    "title": title.strip(),
                    "location": location.strip(),
                    "category": category.strip(),
                    "description": description.strip(),
                    "link": full_link.strip()
                })

                await detail_page.close()

            except Exception as e:
                print(f"⚠️ Error scraping job {i+1}: {e}")
                continue

        await browser.close()

        # Save results
        with open("accor_kenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "location", "category", "description", "link"])
            writer.writeheader()
            writer.writerows(jobs)

        print(f"\n✅ Saved {len(jobs)} jobs to accor_kenya_jobs.csv")

# Run
if __name__ == "__main__":
    asyncio.run(scrape_accor_jobs())
