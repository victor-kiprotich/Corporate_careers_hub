import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import csv

async def scrape_livinggoods_jobs():
    base_url = "https://livinggoods.applytojob.com"
    start_url = f"{base_url}/apply/"
    results = []

    print("🌍 Navigating to Living Goods job board...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(start_url, timeout=60000)

        await page.wait_for_selector("a[href*='/apply/']:not([href$='/apply/'])")

        job_links = await page.locator("a[href*='/apply/']:not([href$='/apply/'])").all()

        print(f"✅ Found {len(job_links)} job(s)")

        for i, job in enumerate(job_links):
            link = await job.get_attribute("href")
            title = (await job.inner_text()).strip()
            full_link = link if link.startswith("http") else base_url + link

            print(f"[{i+1}] Scraping: {title}")

            job_page = await context.new_page()
            await job_page.goto(full_link, timeout=60000)

            html = await job_page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Title
            job_title = soup.find("h1").get_text(strip=True) if soup.find("h1") else title

            # Location
            location_div = soup.find("div", title="Location")
            location = location_div.get_text(strip=True).replace("📍", "") if location_div else "N/A"

            # Role
            role_span = soup.find("span", string=lambda t: t and "ROLE" in t.upper())
            role = role_span.get_text(strip=True) if role_span else "N/A"

            results.append({
                "Title": job_title,
                "Location": location,
                "Role": role,
                "Apply Link": full_link
            })

            await job_page.close()

        await browser.close()

    # Save to CSV
    with open("livinggoods_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Role", "Apply Link"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Saved {len(results)} jobs to livinggoods_jobs.csv")

# Run the scraper
if __name__ == "__main__":
    asyncio.run(scrape_livinggoods_jobs())
