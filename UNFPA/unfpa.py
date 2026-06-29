import asyncio
import csv
from playwright.async_api import async_playwright


async def scrape_estm_jobs():
    base_url = "https://estm.fa.em2.oraclecloud.com"
    jobs_url = (
        base_url + "/hcmUI/CandidateExperience/en/sites/CX_2003/jobs?lastSelectedFacet=LOCATIONS&selectedLocationsFacet=300000000440707"
    )

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Navigating to ESTM Kenya jobs page...")
        await page.goto(jobs_url, timeout=60000)

        # Wait for job cards
        await page.wait_for_selector("a.job-grid-item__link")
        job_links = await page.locator("a.job-grid-item__link").all()

        print(f"✅ Found {len(job_links)} job(s)")

        for i, job_card in enumerate(job_links):
            try:
                link = await job_card.get_attribute("href")
                if not link:
                    continue
                full_link = link if link.startswith("http") else f"{base_url}{link}"

                # Open detail page
                detail_page = await context.new_page()
                await detail_page.goto(full_link, timeout=60000)
                await detail_page.wait_for_selector("h1.job-details__title")

                # Scrape fields
                title = await detail_page.locator("h1.job-details__title").inner_text()

                try:
                    location = await detail_page.locator("span[data-bind='html: primaryLocation']").inner_text()
                except:
                    location = ""

                try:
                    posting_date = await detail_page.locator(".job-meta__subitem").nth(0).inner_text()
                except:
                    posting_date = ""

                try:
                    description = await detail_page.locator(".job-meta__subitem").nth(1).inner_text()
                except:
                    description = ""

                results.append({
                    "Title": title.strip(),
                    "Location": location.strip(),
                    "Posting Date": posting_date.strip(),
                    "Description": description.strip(),
                    "Link": full_link.strip()
                })

                print(f"[{i+1}] Scraped: {title.strip()} - {location.strip()}")
                await detail_page.close()

            except Exception as e:
                print(f"⚠️ Error scraping job {i+1}: {e}")
                continue

        await browser.close()

    # Save to CSV
    with open("estm_kenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Posting Date", "Description", "Link"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Saved {len(results)} jobs to unfpa_kenya_jobs.csv")


if __name__ == "__main__":
    asyncio.run(scrape_estm_jobs())
