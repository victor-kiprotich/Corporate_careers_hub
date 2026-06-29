import csv
from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    print("🌐 Visiting Jumia Kenya Careers page...")
    page.goto("https://group.jumia.com/careers?location=kenya")

    job_cards = page.locator('a.bg-white.flex.shadow-card')
    count = job_cards.count()

    print(f"📌 Found {count} job(s). Scraping...")
    jobs = []

    for i in range(count):
        card = job_cards.nth(i)
        title = card.locator('.title').inner_text()
        link = card.get_attribute("href")
        location = card.locator("p").inner_text()

        # Go to job detail page
        detail_page = context.new_page()
        detail_page.goto(link)

        try:
            detail_page.wait_for_selector("h1.section-header", timeout=10000)
            full_title = detail_page.locator("h1.section-header").inner_text()
            loc_text = detail_page.locator("div.job__location div").inner_text()
            description = detail_page.locator("p").first.inner_text()
        except Exception as e:
            print(f"⚠️ Failed to extract details for {link}: {e}")
            full_title = title
            loc_text = location
            description = ""

        jobs.append({
            "title": full_title,
            "location": loc_text,
            "description": description,
            "link": link
        })

        detail_page.close()

    # Save to CSV
    with open("jumia_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "location", "description", "link"])
        writer.writeheader()
        writer.writerows(jobs)

    print(f"✅ Saved {len(jobs)} job(s) to jumia_jobs.csv")
    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
