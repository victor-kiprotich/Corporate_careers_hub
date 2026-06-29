import asyncio
import csv
from playwright.async_api import async_playwright, TimeoutError

async def scrape_chai_jobs():
    base_url = "https://careers-chai.icims.com"
    iframe_url = f"{base_url}/jobs/search?ss=1&searchLocation=14075--"

    jobs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set to False for debugging
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Navigating to CHAI job listings...")
        await page.goto(iframe_url, timeout=90000)

        # Wait and get iframe
        try:
            frame_element = await page.wait_for_selector('iframe[name="icims_content_iframe"]', timeout=15000)
            frame = await frame_element.content_frame()
        except:
            print("❌ Failed to load iframe.")
            return

        await frame.wait_for_selector('a.iCIMS_Anchor', timeout=30000)
        job_cards = await frame.locator('a.iCIMS_Anchor').all()
        print(f"✅ Found {len(job_cards)} job cards")

        for i, job in enumerate(job_cards):
            try:
                # Get job link
                link = await job.get_attribute("href")
                if not link:
                    print(f"⚠️ Skipping job {i+1}: No link found")
                    continue

                full_link = link if link.startswith("http") else f"{base_url}{link}"

                # Try to get the title safely
                try:
                    title = await job.locator("h3").inner_text(timeout=5000)
                except TimeoutError:
                    title = "Untitled Job"

                print(f"🔍 [{i+1}] Scraping {title}...")

                # Open detail page
                detail_page = await context.new_page()
                await detail_page.goto(full_link, timeout=90000)

                # Wait and extract location
                try:
                    location = await detail_page.locator("dd.iCIMS_JobHeaderData span").inner_text(timeout=5000)
                except:
                    location = "Nairobi"  # fallback

                # Extract description
                try:
                    description = await detail_page.locator("div.description").inner_text(timeout=10000)
                except:
                    try:
                        description = await detail_page.locator("div.iCIMS_JobContent").inner_text(timeout=10000)
                    except:
                        description = "Description not available"

                jobs.append({
                    "Title": title.strip(),
                    "Location": location.strip(),
                    "Description": description.strip(),
                    "Link": full_link.strip()
                })

                await detail_page.close()

            except Exception as e:
                print(f"⚠️ Error scraping job {i+1}: {e}")
                continue

        await browser.close()

    # Save results
    with open("chai_kenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Description", "Link"])
        writer.writeheader()
        writer.writerows(jobs)

    print(f"\n✅ Saved {len(jobs)} jobs to chai_kenya_jobs.csv")


# Run
if __name__ == "__main__":
    asyncio.run(scrape_chai_jobs())
