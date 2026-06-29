import csv
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def scrape_reckitt_jobs():
    base_url = "https://careers.reckitt.com"
    jobs_url = f"{base_url}/search/?createNewAlert=false&q=&locationsearch=kenya"

    results = []
    seen_links = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("Navigating to Reckitt careers Kenya page...")
        page.goto(jobs_url, timeout=60000)
        page.wait_for_timeout(5000)

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        job_links = soup.select("a.jobTitle-link")

        print(f"Found {len(job_links)} job cards before deduplication.")

        for i, link_tag in enumerate(job_links):
            relative_link = link_tag.get("href", "")
            full_link = base_url + relative_link

            if full_link in seen_links:
                continue  # Skip duplicate
            seen_links.add(full_link)

            title = link_tag.text.strip()

            print(f"[{len(results) + 1}] Scraping {title}")

            detail_page = context.new_page()
            detail_page.goto(full_link, timeout=60000)
            detail_page.wait_for_timeout(3000)

            detail_html = detail_page.content()
            detail_soup = BeautifulSoup(detail_html, "html.parser")

            # Extract title from detail page
            title_el = detail_soup.select_one("span[data-careersite-propertyid='title']")
            title = title_el.text.strip() if title_el else title

            # Extract location
            location_el = detail_soup.select_one("span[data-careersite-propertyid='city']")
            location = location_el.text.strip() if location_el else "N/A"

            # Extract description
            desc_el = detail_soup.select_one(
                "#content > div > div.jobDisplayShell > div > div.content > div.job > div:nth-child(5) > div > div > div > span > span > div > div:nth-child(1) > div:nth-child(2) > p"
            )
            description = desc_el.text.strip() if desc_el else "N/A"

            results.append({
                "Title": title,
                "Location": location,
                "Description": description,
                "Link": full_link
            })

            detail_page.close()

        browser.close()

    # Save to CSV
    with open("reckitt_kenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Description", "Link"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Saved {len(results)} unique jobs to reckitt_kenya_jobs.csv")


# Run the scraper
scrape_reckitt_jobs()
