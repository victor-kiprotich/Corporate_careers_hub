import asyncio
import csv
from playwright.async_api import async_playwright

async def scrape_lewis_jobs():
    base_url = "https://lewis.international"
    jobs_url = f"{base_url}/job-dashboard/?job__location_spec=kenya"
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Navigating to Lewis International Kenya jobs...")
        await page.goto(jobs_url, timeout=60000)
        await page.wait_for_selector("a.awsm-job-item")

        job_links = await page.locator("a.awsm-job-item").all()

        print(f"✅ Found {len(job_links)} job(s)")

        for i, job in enumerate(job_links, start=1):
            try:
                link = await job.get_attribute("href")
                full_link = link if link.startswith("http") else f"{base_url}{link}"

                detail_page = await context.new_page()
                await detail_page.goto(full_link, timeout=60000)
                await detail_page.wait_for_selector("h1.entry-title")

                # Extract job title
                title = await detail_page.locator("h1.entry-title").inner_text()

                # Extract job type
                try:
                    job_type = await detail_page.locator(
                        "div.awsm-job-specification-job-type span.awsm-job-specification-term"
                    ).inner_text()
                except:
                    job_type = "N/A"

                # Extract job location (combine all terms)
                try:
                    location_elements = detail_page.locator(
                        "div.awsm-job-specification-job-location span.awsm-job-specification-term"
                    )
                    location_list = await location_elements.all_inner_texts()
                    location = ", ".join([l.strip() for l in location_list])
                except:
                    location = "N/A"

                # Extract job categories (combine all terms)
                try:
                    category_elements = detail_page.locator(
                        "div.awsm-job-specification-job-category span.awsm-job-specification-term"
                    )
                    category_list = await category_elements.all_inner_texts()
                    category = ", ".join([c.strip() for c in category_list])
                except:
                    category = "N/A"

                print(f"[{i}] Scraped: {title} | {location} | {category}")

                results.append({
                    "Title": title,
                    "Type": job_type,
                    "Location": location,
                    "Category": category,
                    "Link": full_link
                })

                await detail_page.close()

            except Exception as e:
                print(f"⚠️ Skipped job {i} due to error: {e}")
                continue

        await browser.close()

    # Save to CSV
    with open("lewis_kenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Type", "Location", "Category", "Link"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Saved {len(results)} job(s) to lewis_kenya_jobs.csv")


# Run the scraper
if __name__ == "__main__":
    asyncio.run(scrape_lewis_jobs())
