import asyncio
import csv
from playwright.async_api import async_playwright

BASE_URL = "https://novapioneer.applytojob.com"
START_URL = f"{BASE_URL}/apply/"
OUTPUT_FILE = "nova_kenya_jobs.csv"

async def get_job_details(context, url):
    try:
        page = await context.new_page()
        await page.goto(url, timeout=60000)

        # Extract location and job type
        location = await page.locator('div[title="Location"]').text_content() or "N/A"
        job_type = await page.locator('div[title="Type"]').text_content() or "N/A"

        # Extract first paragraph of job description
        await page.wait_for_selector("#job-description p", timeout=10000)
        desc = await page.locator("#job-description p").nth(0).text_content() or "N/A"

        await page.close()
        return location.strip(), job_type.strip(), desc.strip()
    except Exception as e:
        print(f"⚠️ Error on detail page {url}: {e}")
        return "N/A", "N/A", "N/A"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(START_URL, timeout=60000)
        await page.wait_for_selector("a", timeout=10000)

        job_links = await page.locator("a[href*='/apply/']:not([href^='#'])").all()
        print(f"🔍 Found {len(job_links)} total jobs.")

        results = []
        for i, link in enumerate(job_links):
            try:
                title = (await link.text_content()).strip()
                href = await link.get_attribute("href")
                if not href:
                    continue
                full_url = href if href.startswith("http") else f"{BASE_URL}{href}"

                # Check if job is located in Kenya
                container = link.locator("xpath=..").locator("xpath=..")
                tags = await container.locator("ul li").all_text_contents()
                if not any("Kenya" in tag for tag in tags):
                    continue

                print(f"🔎 Scraping ({i+1}): {title}")
                location, job_type, description = await get_job_details(context, full_url)

                results.append({
                    "Job Title": title,
                    "Location": location,
                    "Type": job_type,
                    "Apply Link": full_url,
                    "Description": description
                })

            except Exception as e:
                print(f"⚠️ Skipping job {i+1} due to error: {e}")

        # Write results to CSV
        with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Job Title", "Location", "Type", "Apply Link", "Description"])
            writer.writeheader()
            writer.writerows(results)

        print(f"\n✅ Done! Saved {len(results)} Kenyan job(s) to {OUTPUT_FILE}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
