import asyncio
import csv
from playwright.async_api import async_playwright

BASE_URL = "https://www.m-kopa.com"
START_URL = f"{BASE_URL}/careers"
OUTPUT_FILE = "m_kopa_jobs.csv"
NAIROBI_ID = "ed2d7763-f433-4318-abeb-919068213c32"

async def extract_job_details(context, job_url, title_from_main, meta_text):
    try:
        page = await context.new_page()
        await page.goto(job_url, timeout=60000)

        # Extract location, type, and department from meta_text
        parts = [part.strip() for part in meta_text.split("•")]
        department = parts[0] if len(parts) > 0 else "N/A"
        location = parts[1] if len(parts) > 1 else "N/A"
        emp_type = parts[2] if len(parts) > 2 else "N/A"

        # Description from 3rd paragraph in overview
        try:
            await page.wait_for_selector("#overview p", timeout=10000)
            paragraphs = await page.locator("#overview p").all()
            description = await paragraphs[2].text_content() if len(paragraphs) > 2 else "N/A"
        except:
            description = "N/A"

        await page.close()

        return {
            "Job Title": title_from_main.strip(),
            "Location": location.strip(),
            "Type": emp_type.strip(),
            "Department": department.strip(),
            "Description": 'Click the link for the description',
            "Apply Link": job_url
        }

    except Exception as e:
        print(f"⚠️ Failed to extract job detail from {job_url}: {e}")
        return None

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌐 Navigating to M-KOPA careers page...")
        await page.goto(START_URL, timeout=60000)

        await page.wait_for_selector("iframe[title='Ashby Job Board']", timeout=15000)
        iframe = page.frame_locator("iframe[title='Ashby Job Board']")

        print("🎯 Selecting Nairobi from location filter...")
        await iframe.locator("select[aria-label='Location']").select_option(NAIROBI_ID)
        await asyncio.sleep(3)  # Allow time for jobs to load

        print("🔍 Extracting job links...")
        job_cards = await iframe.locator("a._container_j2da7_1").all()

        print(f"📌 Found {len(job_cards)} Nairobi job(s). Scraping...")
        results = []

        for i, card in enumerate(job_cards):
            try:
                href = await card.get_attribute("href")
                full_link = href if href.startswith("http") else f"{BASE_URL}{href}"

                # Title from the job card
                title = await card.locator("h3").text_content()

                # Metadata text containing dept, location(s), and type
                meta = await card.locator("._details_12ylk_389 p").text_content()

                print(f"🔎 [{i+1}] {title.strip()} — {full_link}")
                job_data = await extract_job_details(context, full_link, title, meta)

                if job_data:
                    results.append(job_data)

            except Exception as e:
                print(f"⚠️ Skipped job {i+1} due to error: {e}")

        # Save to CSV
        if results:
            with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "Job Title", "Location", "Type", "Department", "Apply Link", "Description"
                ])
                writer.writeheader()
                writer.writerows(results)

            print(f"\n✅ Done! Saved {len(results)} job(s) to {OUTPUT_FILE}")
        else:
            print("❌ No job data extracted.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
