import csv
from playwright.sync_api import sync_playwright

def scrape_google_nairobi_jobs():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://www.google.com/about/careers/applications/jobs/results/?location=Nairobi%20Kenya", timeout=60000)
        page.wait_for_selector("div.sMn82b", timeout=15000)

        jobs = page.locator("div.sMn82b")
        count = jobs.count()
        print(f"📌 Found {count} job(s)")

        job_list = []

        for i in range(count):
            job = jobs.nth(i)

            title = job.locator("h3.QJPWVe").first.inner_text()
            location = job.locator("span.r0wTof").first.inner_text()
            description = job.locator("div.Xsxa1e").first.inner_text()
            partial_link = job.locator("a.WpHeLc").first.get_attribute("href")
            full_link = f"https://www.google.com/about/careers/applications/{partial_link}" if partial_link else "N/A"

            job_list.append({
                "title": title,
                "location": location,
                "description": description,
                "link": full_link
            })

        # Save to CSV
        with open("google_nairobi_jobs.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "location", "description", "link"])
            writer.writeheader()
            writer.writerows(job_list)

        print(f"✅ Done. Saved {len(job_list)} jobs to 'google_nairobi_jobs.csv'")
        browser.close()

scrape_google_nairobi_jobs()
