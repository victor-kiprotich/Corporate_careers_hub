import csv
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def scrape_acdivoca_jobs():
    base_url = "https://internationaljobs-acdivoca.icims.com"
    jobs_url = f"{base_url}/jobs/search?ss=1&hashed=-435626115"

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("🌍 Navigating to ACDI/VOCA job board...")
        page.goto(jobs_url, timeout=60000)

        # ✅ Correct way to access iframe content in sync mode
        frame = page.frame(name="icims_content_iframe")
        if not frame:
            print("❌ Could not access iframe content.")
            browser.close()
            return

        try:
            frame.wait_for_selector("div.iCIMS_Expandable_Container", timeout=15000)
        except:
            print("❌ No job listings found.")
            browser.close()
            return

        html = frame.content()
        soup = BeautifulSoup(html, "html.parser")
        job_cards = soup.select("div.iCIMS_Expandable_Container")

        kenya_jobs = []

        for card in job_cards:
            location_el = card.select_one("li.iCIMS_JobHeaderData span.jobLocation")
            location = location_el.text.strip() if location_el else ""

            if "kenya" in location.lower():
                title_el = card.select_one("a.iCIMS_Anchor h3")
                title = title_el.text.strip() if title_el else "N/A"

                link_el = card.select_one("a.iCIMS_Anchor")
                relative_link = link_el["href"] if link_el else ""
                full_link = base_url + relative_link

                desc_el = card.select_one("div.iCIMS_Expandable_Text")
                description = desc_el.text.strip() if desc_el else "N/A"

                kenya_jobs.append({
                    "Title": title,
                    "Location": location,
                    "Description": description,
                    "Link": full_link
                })

        browser.close()

        if not kenya_jobs:
            print("❌ No Kenya-based jobs found.")
            return

        print(f"✅ Found {len(kenya_jobs)} Kenya-based job(s)")

        with open("acdivoca_kenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Description", "Link"])
            writer.writeheader()
            writer.writerows(kenya_jobs)

        print("✅ Saved to acdivoca_kenya_jobs.csv")


# Run the scraper
scrape_acdivoca_jobs()
