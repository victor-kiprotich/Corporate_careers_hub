import csv
from playwright.sync_api import sync_playwright

CAREERS_URL = "https://carrefour-careers.pages.dev/#openings"

def run(playwright):
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    print("🌐 Visiting Carrefour Careers page...")
    page.goto(CAREERS_URL)
    page.wait_for_timeout(3000)

    titles = page.locator("div.font-bold.text-xl")
    descriptions = page.locator("p.text-muted.mt-2")

    count = titles.count()
    print(f"📌 Found {count} job(s). Scraping...")

    jobs = []

    for i in range(count):
        title = titles.nth(i).inner_text().strip()
        try:
            description = descriptions.nth(i).inner_text().strip()
        except:
            description = ""

        jobs.append({
            "title": title,
            "description": description,
            "link": CAREERS_URL
        })

    # Save to CSV
    with open("carrefour_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "description", "link"])
        writer.writeheader()
        writer.writerows(jobs)

    print(f"✅ Saved {len(jobs)} job(s) to carrefour_jobs.csv")

    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
