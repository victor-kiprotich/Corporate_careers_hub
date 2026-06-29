import csv
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_millar_cameron_jobs():
    base_url = "https://millarcameron.com"
    jobs_url = f"{base_url}/our-latest-jobs"
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Change to True to run headless
        context = browser.new_context()
        page = context.new_page()

        print("🌍 Navigating to Millar Cameron jobs page...")
        page.goto(jobs_url, timeout=60000)
        page.wait_for_timeout(3000)

        soup = BeautifulSoup(page.content(), "html.parser")

        job_cards = soup.select("a.c-job-listing__item-link")
        print(f"✅ Found {len(job_cards)} total job cards")

        for i, card in enumerate(job_cards):
            location = card.select_one("span.c-job-listing__item-data")
            location_text = location.get_text(strip=True) if location else ""

            if "kenya" not in location_text.lower():
                continue  # skip if not in Kenya

            title_el = card.select_one("h2.c-job-listing__item-title")
            category_el = card.select_one("span.c-job-listing__item-sub-title")
            link = card.get("href")

            job = {
                "Title": title_el.get_text(strip=True) if title_el else "N/A",
                "Category": category_el.get_text(strip=True) if category_el else "N/A",
                "Location": location_text,
                "Link": base_url + link if link else "N/A"
            }

            print(f"📄 [{i+1}] {job['Title']}")
            results.append(job)

        browser.close()

    # Save to CSV
    with open("millar_cameron_kenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Category", "Location", "Link"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Saved {len(results)} Kenya-based jobs to millar_cameron_kenya_jobs.csv")

# Run the scraper
scrape_millar_cameron_jobs()
