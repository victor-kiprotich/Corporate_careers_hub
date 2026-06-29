import asyncio
import csv
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from playwright.async_api import async_playwright

BASE_URL = "https://job-boards.greenhouse.io"
JOBS_URL = f"{BASE_URL}/americaninstitutesforresearch?offices%5B%5D=4019330008"

async def scrape_job_detail(context, job_url):
    try:
        page = await context.new_page()
        await page.goto(job_url, timeout=60000)
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        title = soup.select_one("h1").get_text(strip=True)
        location_el = soup.select_one("div.location")
        location = location_el.get_text(strip=True) if location_el else "Not specified"

        description_el = soup.select_one("div#content")
        description = description_el.get_text(separator="\n", strip=True) if description_el else ""

        await page.close()

        return {
            "Title": title,
            "Location": location,
            "Description": description,
            "Link": job_url
        }
    except Exception as e:
        print(f"❌ Failed to scrape {job_url}: {e}")
        return None

async def run_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌐 Loading job listings page...")
        await page.goto(JOBS_URL, timeout=60000)

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        job_cards = soup.select("td.cell a")

        print(f"🔍 Found {len(job_cards)} job(s).")

        job_links = [urljoin(BASE_URL, card.get("href")) for card in job_cards if card.get("href")]

        results = []
        for i, job_link in enumerate(job_links, 1):
            print(f"🔎 Scraping job {i}/{len(job_links)}: {job_link}")
            job_data = await scrape_job_detail(context, job_link)
            if job_data:
                results.append(job_data)

        await browser.close()

        with open("air_nairobi_jobs.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Description", "Link"])
            writer.writeheader()
            writer.writerows(results)

        print(f"\n✅ Saved {len(results)} jobs to 'air_nairobi_jobs.csv'")

if __name__ == "__main__":
    asyncio.run(run_scraper())
