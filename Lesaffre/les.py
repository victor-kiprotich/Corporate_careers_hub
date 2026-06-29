import asyncio
import csv
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def scrape_lesaffre_kenya_jobs():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌐 Navigating to Lesaffre Kenya jobs...")
        await page.goto("https://www.lesaffre.com/careers/jobs/?keywords&country%5B0%5D=Kenya", timeout=60000)

        # Wait for job cards
        await page.wait_for_selector("a[data-id]")
        job_links = await page.locator("a[data-id]").all()
        print(f"✅ Found {len(job_links)} job(s)")

        jobs = []

        for job in job_links:
            try:
                title = await job.inner_text()
                relative_link = await job.get_attribute("href")
                full_link = f"https://www.lesaffre.com{relative_link}" if relative_link.startswith("/") else relative_link

                detail_page = await context.new_page()
                await detail_page.goto(full_link, timeout=60000)
                await detail_page.wait_for_selector("h1.entry-title")

                job_title = await detail_page.locator("h1.entry-title").inner_text()

                try:
                    category = await detail_page.locator("dd").first.inner_text()
                except:
                    category = "N/A"

                try:
                    html_content = await detail_page.locator("div.col-xs-12.col-md-9").inner_html()
                    soup = BeautifulSoup(html_content, "html.parser")
                    description = soup.get_text(separator="\n", strip=True)
                except:
                    description = "N/A"

                jobs.append({
                    "title": job_title.strip(),
                    "category": category.strip(),
                    "description": description.strip(),
                    "apply_link": full_link
                })

                print(f"📄 {job_title}")
                await detail_page.close()

            except Exception as e:
                print(f"⚠️ Error scraping job: {e}")

        # Save to CSV
        with open("lesaffre_kenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "category", "description", "apply_link"])
            writer.writeheader()
            writer.writerows(jobs)

        print(f"\n✅ Saved {len(jobs)} jobs to lesaffre_kenya_jobs.csv")
        await browser.close()

# Run the async scraper
asyncio.run(scrape_lesaffre_kenya_jobs())
