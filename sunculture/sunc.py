import csv
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    base_url = "https://sunculture.freshteam.com"
    job_board_url = f"{base_url}/jobs"

    page.goto(job_board_url, timeout=60000)
    page.wait_for_timeout(3000)

    html = page.content()
    soup = BeautifulSoup(html, "html.parser")

    job_cards = soup.select("a.heading.show")

    results = []

    for card in job_cards:
        location = card.get("data-portal-location", "")
        if location != "Nairobi, Kenya":
            continue

        title = card.get("data-portal-title", "").replace("&amp;", "&")
        href = card.get("href", "")
        link = base_url + href

        detail_page = context.new_page()
        detail_page.goto(link, timeout=30000)
        detail_page.wait_for_timeout(2000)

        detail_html = detail_page.content()
        detail_soup = BeautifulSoup(detail_html, "html.parser")

        # Get first long description span (like the one you showed)
        description_el = detail_soup.select_one("div.job-show-content span[style*='font-size']")
        description = description_el.get_text(separator=" ", strip=True) if description_el else ""

        results.append({
            "Title": title,
            "Location": location,
            "Description": title,
            "Link": link

        })

        print(f"Scraped: {title} - {location}")
        detail_page.close()

    # Save to CSV
    with open("sunculture_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Link", "Description"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Saved {len(results)} jobs to sunculture_jobs.csv")
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
