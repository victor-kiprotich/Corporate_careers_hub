import csv
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless= True)
    context = browser.new_context()
    page = context.new_page()

    url = "https://job-boards.greenhouse.io/oafkenya"
    base_url = "https://job-boards.greenhouse.io"

    page.goto(url, timeout=60000)
    page.wait_for_timeout(3000)

    html = page.content()
    soup = BeautifulSoup(html, "html.parser")

    job_cards = soup.select("td.cell")

    results = []

    for card in job_cards:
        link_tag = card.find("a")
        location_tag = card.find("p", class_="body body__secondary body--metadata")
        if not link_tag:
            continue

        title = link_tag.get_text(strip=True)
        relative_link = link_tag.get("href", "")
        full_link = base_url + relative_link if relative_link.startswith("/") else relative_link

        location = location_tag.get_text(strip = True) if location_tag else "Not specified"


        # Open job detail page
        detail_page = context.new_page()
        detail_page.goto(full_link, timeout=30000)
        detail_page.wait_for_timeout(2000)

        detail_html = detail_page.content()
        detail_soup = BeautifulSoup(detail_html, "html.parser")

        # Get the first paragraph in the content area for job description
        description_el = detail_soup.select_one("p[data-pm-slice]")
        description = description_el.get_text(separator=" ", strip=True) if description_el else ""

        results.append({
            "Title": title,
            "Location": location,
            "Description": description,
            "Link": full_link
        })

        print(f"Scraped: {title} - {location}")
        detail_page.close()

    # Save to CSV
    with open("oafkenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Link", "Description"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Saved {len(results)} jobs to oafkenya_jobs.csv")
    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
