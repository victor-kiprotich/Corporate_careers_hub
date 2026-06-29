import csv
from playwright.sync_api import Playwright, sync_playwright

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    print("🌐 Visiting Airtel Kenya careers page...")
    page.goto("https://www.airtelkenya.com/vacancies")

    # Extract job titles and links
    jobs = []
    job_cards = page.locator("ul.job-list > li > a")
    count = job_cards.count()

    if count == 0:
        print("❌ No jobs found.")
    else:
        for i in range(count):
            job = job_cards.nth(i)
            title = job.inner_text().strip()
            link = job.get_attribute("href")
            if link and not link.startswith("http"):
                link = "https://www.airtelkenya.com" + link
            jobs.append({"title": title, "link": link})

        # Save to CSV
        with open("airtel_jobs.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "link"])
            writer.writeheader()
            writer.writerows(jobs)

        print(f"✅ Saved {len(jobs)} job(s) to airtel_jobs.csv")

    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)

