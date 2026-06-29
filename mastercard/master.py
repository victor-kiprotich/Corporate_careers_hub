import asyncio
import csv
from playwright.async_api import async_playwright

async def scrape_mastercard_jobs():
    base_url = "https://mastercardfoundation.wd10.myworkdayjobs.com"
    jobs_url = base_url + "/en-US/mastercardfdn/jobs?locationCountry=9e684fd7be1e469d9ee955a4c3b754be"

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(jobs_url, timeout=60000)

        # Wait for job cards to load
        await page.wait_for_selector("a.css-19uc56f", timeout=30000)
        job_cards = await page.query_selector_all("a.css-19uc56f")

        print(f"Found {len(job_cards)} job(s)")

        for i, card in enumerate(job_cards):
            title_el = await card.query_selector("h2")
            job_title = await title_el.inner_text() if title_el else ""
            job_link = await card.get_attribute("href")
            full_link = base_url + job_link if job_link else ""

            # Open detail page
            detail_page = await context.new_page()
            await detail_page.goto(full_link, timeout=30000)

            # Extract job title from detail page
            try:
                await detail_page.wait_for_selector("h2[data-automation-id='jobPostingHeader']", timeout=15000)
                job_title_el = await detail_page.query_selector("h2[data-automation-id='jobPostingHeader']")
                job_title = await job_title_el.inner_text() if job_title_el else job_title
            except:
                pass

            # Extract location
            try:
                location_el = await detail_page.query_selector("div[data-automation-id='locations'] dd")
                location = await location_el.inner_text() if location_el else ""
            except:
                location = ""

            # Extract end date
            try:
                end_date_el = await detail_page.query_selector("div[data-automation-id='timeLeftToApply'] dd")
                end_date = await end_date_el.inner_text() if end_date_el else ""
            except:
                end_date = ""

            results.append({
                "Title": job_title.strip(),
                "Location": 'Kenya',
                "End Date": end_date.strip(),
                "Link": full_link.strip()
            })

            print(f"[{i+1}] {job_title.strip()} - {location.strip()}")

            await detail_page.close()

        await browser.close()

    # Save to CSV
    keys = ["Title", "Location", "End Date", "Link"]
    with open("mastercard_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)

    print(f"Saved {len(results)} jobs to mastercard_jobs.csv")
    return results


if __name__ == "__main__":
    asyncio.run(scrape_mastercard_jobs())
