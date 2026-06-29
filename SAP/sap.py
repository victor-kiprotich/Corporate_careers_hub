import asyncio
import csv
from playwright.async_api import async_playwright

BASE_URL = "https://jobs.sap.com"
START_URL = f"{BASE_URL}/go/SAP-Jobs-in-Africa/1307101/?location=KE"
OUTPUT_FILE = "sap_nairobi_jobs.csv"

async def extract_job_details(context, url):
    try:
        page = await context.new_page()
        await page.goto(url, timeout=60000)

        # Title
        title_el = page.locator('[data-careersite-propertyid="title"]')
        title = await title_el.text_content()

        # Location
        location_el = page.locator(".jobGeoLocation")
        location = await location_el.text_content()

        # Department
        dept_el = page.locator('[data-careersite-propertyid="department"]')
        department = await dept_el.nth(0).text_content()

        # Posting Date
        date_el = page.locator('[data-careersite-propertyid="date"]')
        posting_date = await date_el.text_content()

        # Description: first paragraph
        try:
            await page.wait_for_selector("div#jobDescriptionSection p", timeout=7000)
            paragraphs = await page.locator("div#jobDescriptionSection p").all()
            description = await paragraphs[0].text_content() if paragraphs else "N/A"
        except:
            # Fallback to styled span if <p> tags aren't used
            try:
                await page.wait_for_selector("span[style*='font-size:10.0pt']", timeout=5000)
                description = await page.locator("span[style*='font-size:10.0pt']").nth(0).text_content()
            except:
                description = "N/A"


        await page.close()

        return {
            "Job Title": title.strip() if title else "N/A",
            "Location": location.strip() if location else "N/A",
            "Department": department.strip() if department else "N/A",
            "Posting Date": posting_date.strip() if posting_date else "N/A",
            "Description": description.strip() if description else "N/A",
            "Apply Link": url
        }

    except Exception as e:
        print(f"❌ Failed to scrape {url}: {e}")
        return None

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Opening SAP Africa job board...")
        await page.goto(START_URL, timeout=60000)
        await page.wait_for_selector("tr.data-row", timeout=15000)

        job_rows = await page.locator("tr.data-row").all()
        print(f"📌 Found {len(job_rows)} job card(s)... Checking location = Nairobi")

        results = []
        seen_links = set()

        for i, row in enumerate(job_rows):
            try:
                title_el = row.locator("a.jobTitle-link").first
                title = await title_el.text_content()
                href = await title_el.get_attribute("href")
                full_url = f"{BASE_URL}{href}"

                if full_url in seen_links:
                    continue
                seen_links.add(full_url)

                # Open detail page to confirm Nairobi location
                detail_page = await context.new_page()
                await detail_page.goto(full_url, timeout=60000)
                location = await detail_page.locator(".jobGeoLocation").text_content()
                await detail_page.close()

                if "Nairobi" not in location:
                    continue

                print(f"🔎 [{len(results)+1}] Scraping: {title.strip()}")
                job_data = await extract_job_details(context, full_url)

                if job_data:
                    results.append(job_data)

            except Exception as e:
                print(f"⚠️ Skipping row {i+1}: {e}")

        # Save to CSV
        if results:
            with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "Job Title", "Location", "Department", "Posting Date", "Description", "Apply Link"
                ])
                writer.writeheader()
                writer.writerows(results)

            print(f"\n✅ Done! Saved {len(results)} Nairobi job(s) to {OUTPUT_FILE}")
        else:
            print("❌ No Nairobi jobs found.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
