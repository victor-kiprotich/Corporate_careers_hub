from playwright.sync_api import sync_playwright
import csv

OUTPUT_FILE = "kra_jobs.csv"
BASE_URL = "https://www.kra.go.ke"

def run(playwright):
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    print("🌐 Navigating to KRA Careers page...")
    page.goto("https://www.kra.go.ke/careers", timeout=60000)

    print("🔗 Clicking 'View Job Openings'...")
    page.get_by_role("link", name="View Job Openings").click()

    # Wait for job cards to load on the redirected page
    page.wait_for_selector("div.doc-title", timeout=30000)

    print("📄 Scraping job cards...")

    job_blocks = page.locator("div.doc-title").all()
    closing_date_blocks = page.locator("p.subtitle", has_text="Closing Date").all()
    detail_links = page.locator("a.btn.btn-style-3", has_text="View Details").all()

    results = []

    for i in range(min(len(job_blocks), len(closing_date_blocks), len(detail_links))):
        try:
            title = job_blocks[i].locator("p").nth(1).inner_text().strip()
            closing_date_label = closing_date_blocks[i]
            closing_date = closing_date_label.locator("xpath=following-sibling::p").first.inner_text().strip()
            href = detail_links[i].get_attribute("href")
            full_link = href if href.startswith("http") else f"{BASE_URL}{href}"

            results.append({
                "Job Title": title,
                "Closing Date": closing_date,
                "Detail Link": full_link
            })

            print(f"✅ {title} | Closing: {closing_date}")

        except Exception as e:
            print(f"⚠️ Skipped a job due to error: {e}")

    # Save to CSV
    with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Job Title", "Closing Date", "Detail Link"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n📁 Saved {len(results)} jobs to {OUTPUT_FILE}")
    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
