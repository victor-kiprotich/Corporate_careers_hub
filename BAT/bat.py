import asyncio
import csv
from playwright.async_api import async_playwright

async def scrape_bat_jobs():
    url = "https://careers.bat.com/en/search-jobs/Kenya/1045/2/192950/1/38/50/2"
    base_url = "https://careers.bat.com"

    jobs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Navigating to BAT Kenya jobs page...")
        await page.goto(url, timeout=60000)
        await page.wait_for_selector("a[data-job-id]")

        job_cards = await page.locator("a[data-job-id]").all()
        print(f"✅ Found {len(job_cards)} job cards")

        for i, card in enumerate(job_cards):
            try:
                relative_link = await card.get_attribute("href")
                full_link = base_url + relative_link

                detail_page = await context.new_page()
                await detail_page.goto(full_link, timeout=60000)
                await detail_page.wait_for_selector("h1.ajd_header__job-title")

                title = await detail_page.locator("h1.ajd_header__job-title").inner_text()
                location = await detail_page.locator("p.ajd_header__location").inner_text()
                
                try:
                    job_type = await detail_page.locator("div.ajd-job-info-item span.ajd-job-info").inner_text()
                except:
                    job_type = "N/A"

                try:
                    description = await detail_page.locator("div.text-inner").inner_text()
                except:
                    description = "N/A"

                print(f"📄 Scraped: {title.strip()}")

                jobs.append({
                    "Title": title.strip(),
                    "Location": location.strip(),
                    "Job Type": job_type.strip(),
                    "Description": description.strip(),
                    "Link": full_link.strip()
                })

                await detail_page.close()

            except Exception as e:
                print(f"⚠️ Error scraping job {i + 1}: {e}")
                continue

        await browser.close()

        # Save to CSV
        with open("bat_kenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Job Type", "Description", "Link"])
            writer.writeheader()
            writer.writerows(jobs)

        print(f"\n✅ Saved {len(jobs)} jobs to bat_kenya_jobs.csv")

# Run
asyncio.run(scrape_bat_jobs())
