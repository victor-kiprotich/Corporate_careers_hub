import asyncio
import csv
from playwright.async_api import async_playwright

OUTPUT_FILE = "au_jobs.csv"
BASE_URL = "https://jobs.au.int"

async def scrape_job_detail(context, url):
    try:
        detail_page = await context.new_page()
        await detail_page.goto(url, timeout=60000)

        # Locate the first paragraph under the Purpose of Job section
        first_paragraph = detail_page.locator(
            "div[style*='padding:10.0px'] > div:nth-of-type(2) > p"
        ).first

        await first_paragraph.wait_for(state="visible", timeout=10000)
        desc = await first_paragraph.text_content()
        await detail_page.close()

        return desc.strip() if desc else "N/A"
    except Exception as e:
        print(f"⚠️ Failed to scrape detail at {url}: {e}")
        return "N/A"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌐 Opening AU Careers filtered for Kenya...")
        await page.goto("https://jobs.au.int/search/?searchResultView=LIST&markerViewed=&carouselIndex=&facetFilters=%7B%22mfield1%22%3A%5B%22Kenya%22%5D%7D&pageNumber=0")

        try:
            await page.wait_for_selector("li.JobsList_jobCard__8wE-Z", timeout=15000)
            job_cards = page.locator("li.JobsList_jobCard__8wE-Z")
            count = await job_cards.count()
        except Exception as e:
            print(f"⚠️ No job cards found or timed out: {e}")
            count = 0

        print(f"🔍 Found {count} Kenyan job(s).")

        results = []
        for i in range(count):
            try:
                card = job_cards.nth(i)
                title_el = card.locator("a.jobCardTitle")
                title = await title_el.text_content()
                href = await title_el.get_attribute("href")
                full_link = BASE_URL + href if href else "N/A"

                title_str = title.strip() if title else "N/A"
                print(f"🔎 Scraping job {i+1}: {title_str}")

                # Visit job detail page
                description = await scrape_job_detail(context, full_link)

                results.append({
                    "Job Title": title_str,
                    "Location": "Kenya",
                    "Apply Link": full_link,
                    "Description": description
                })
            except Exception as e:
                print(f"⚠️ Skipped job {i+1} due to error: {e}")

        # Save to CSV
        with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Job Title", "Location", "Apply Link", "Description"])
            writer.writeheader()
            writer.writerows(results)

        print(f"\n✅ Saved {len(results)} job(s) to {OUTPUT_FILE}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
