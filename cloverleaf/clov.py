from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import csv

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Go to the job listings page
    page.goto("https://cloverleaf-care.breezy.hr/")
    page.get_by_role("link", name="View Openings").click()
    page.wait_for_timeout(3000)

    # Get the rendered HTML content
    html = page.content()
    soup = BeautifulSoup(html, "html.parser")

    job_cards = soup.select("li.position.transition")
    results = []

    for card in job_cards:
        location_li = card.select_one("li.location")
        if not location_li:
            continue

        spans = location_li.select("span")
        if (
            len(spans) >= 2 and
            spans[0].get_text(strip=True) == "Pan Kenya, KE" 
        ):
            # Extract title
            title_el = card.select_one("a h2")
            title = title_el.get_text(strip=True) if title_el else ""

            # Extract department
            department_el = card.select_one("li.department span")
            department = department_el.get_text(strip=True) if department_el else ""

            # Extract job link
            link_el = card.select_one("a")
            link = "https://cloverleaf-care.breezy.hr" + link_el["href"] if link_el else ""

            # Store result
            results.append({
                "Title": title,
                "Location": "Pan Kenya, KE / Remote (any location)",
                "Department": department,
                "Link": link
            })

    # Save to CSV
    with open("cloverleaf_kenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Department", "Link"])
        writer.writeheader()
        writer.writerows(results)

    print(f"Saved {len(results)} job(s) to cloverleaf_kenya_jobs.csv")

    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
