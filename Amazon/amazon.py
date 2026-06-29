import csv
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.amazon.jobs"
SEARCH_URL = f"{BASE_URL}/en/search?base_query=&loc_query=Kenya&country=KEN"

def run(playwright):
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    print("🌐 Visiting Amazon Kenya jobs page...")
    page.goto(SEARCH_URL)
    page.wait_for_selector("a.job-link")

    job_links = page.locator("a.job-link")
    total = job_links.count()
    print(f"📌 Found {total} job(s). Scraping...")

    jobs = []

    for i in range(total):
        job_url_suffix = job_links.nth(i).get_attribute("href")
        job_url = BASE_URL + job_url_suffix

        job_page = context.new_page()
        job_page.goto(job_url)

        try:
            job_page.wait_for_selector("h1.title", timeout=10000)

            title = job_page.locator("h1.title").inner_text().strip()
            location = job_page.locator("div.location-icon ul li").inner_text().strip()
            description = job_page.locator("#job-detail-body > div > div.col-12.col-md-7.col-lg-8.col-xl-9 > div > div:nth-child(2) > p").inner_text().strip()

            jobs.append({
                "title": title,
                "location": location,
                "description": description,
                "link": job_url
            })
            print(f"✅ Scraped: {title}")
        except Exception as e:
            print(f"⚠️ Failed to scrape job {i+1}: {e}")
        finally:
            job_page.close()

    # Save to CSV
    with open("amazon_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "location", "description", "link"])
        writer.writeheader()
        writer.writerows(jobs)

    print(f"\n✅ Done! Saved {len(jobs)} job(s) to amazon_jobs.csv")
    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
