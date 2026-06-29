import asyncio
import csv
from playwright.async_api import async_playwright

OUTPUT_FILE = "heineken_jobs.csv"
BASE_URL = "https://careers.theheinekencompany.com"

async def scrape_job_detail(context, url):
    try:
        page = await context.new_page()
        await page.goto(url, timeout=60000)
        await page.wait_for_selector("p[style='text-align:justify']", timeout=10000)
        description = await page.locator("p[style='text-align:justify']").first.text_content()
        await page.close()
        return description.strip() if description else "N/A"
    except Exception as e:
        print(f"⚠️ Failed to scrape job at {url}: {e}")
        return "N/A"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌐 Navigating to Heineken Careers...")
        await page.goto("https://agegate.theheinekencompany.com/agegateway?oru=https%3a%2f%2fcareers.theheinekencompany.com%2fsearch%2f%3fcreateNewAlert%3dfalse%26q%3d%26locationsearch%3dkenya&opco=search&returnurl=%2f?oru%3dhttps%253a%252f%252fcareers.theheinekencompany.com%252fsearch%252f%253fcreateNewAlert%253dfalse%2526q%253d%2526locationsearch%253dkenya%26opco%3dsearch", timeout=60000)

        # Age verification form
        await page.get_by_role("textbox", name="Country").click()
        await page.get_by_role("textbox", name="Country").fill("K")

        kenya_option = page.locator("li", has_text="Kenya")
        await kenya_option.wait_for(state="visible", timeout=10000)
        await kenya_option.click()

        await page.get_by_placeholder("DD").fill("11")
        await page.get_by_placeholder("MM").fill("11")
        await page.get_by_placeholder("YY").fill("2000")
        await page.get_by_role("button", name="Enter").click()

        # Wait for Search Jobs button and click
        await page.wait_for_selector("tr.data-row", timeout=10000)
        await page.locator("tr.data-row").nth(0).click()
        await page.wait_for_timeout(5000)

        print("🔍 Collecting Kenyan job postings...")

        job_links = await page.locator("a.jobTitle-link").all()
        print(f"🔎 Found {len(job_links)} jobs")

        results = []

        for i, job_link in enumerate(job_links):
            try:
                title = await job_link.text_content()
                href = await job_link.get_attribute("href")
                full_link = f"{BASE_URL}{href}" if href.startswith("/") else href

                print(f"🔎 Scraping job {i+1}: {full_link}")

                # Open detail page and extract description
                description = await scrape_job_detail(context, full_link)

                # Open job detail again for other info
                detail_page = await context.new_page()
                await detail_page.goto(full_link, timeout=60000)
                body_text = await detail_page.locator("p").all_text_contents()
                body_html = await detail_page.content()

                # Extract location and closing date from <p> tag
                closing_date = "N/A"
                location = "N/A"
                try:
                    para_texts = await detail_page.locator("p").all_text_contents()
                    for text in para_texts:
                        if "Location:" in text:
                            location = text.split("Location:")[1].split("\n")[0].strip()
                        if "Closing Date:" in text:
                            closing_date = text.split("Closing Date:")[1].strip()
                except:
                    pass

                await detail_page.close()

                results.append({
                    "Job Title": title.strip() if title else "N/A",
                    "Location": location,
                    "Closing Date": closing_date,
                    "Apply Link": full_link,
                    "Description": description
                })

            except Exception as e:
                print(f"⚠️ Failed to scrape job {i+1}: {e}")

        # Save to CSV
        with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Job Title", "Location", "Closing Date", "Apply Link", "Description"])
            writer.writeheader()
            writer.writerows(results)

        print(f"\n✅ Saved {len(results)} jobs to {OUTPUT_FILE}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
