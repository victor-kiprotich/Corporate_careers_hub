import csv
from datetime import datetime
from playwright.sync_api import Playwright, sync_playwright, TimeoutError as PlaywrightTimeoutError

CAREERS_URL = "https://sic.co.ke/careers/"
CSV_FILE = "sic_jobs.csv"


def parse_date(text: str) -> str:
    """
    Try to parse a human date like 'July 15, 2025' into YYYY-MM-DD.
    Return original text if parsing fails.
    """
    text = text.strip()
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return text  # fallback


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    print("🌍 Navigating to SIC Careers...")
    page.goto(CAREERS_URL, timeout=60000)

    # Wait for Elementor loop items that hold jobs
    page.wait_for_selector("div.e-loop-item.job, article.job", timeout=30000)

    job_cards = page.locator("div.e-loop-item.job, article.job")
    total = job_cards.count()
    print(f"✅ Found {total} job card(s).")

    jobs = []

    for i in range(total):
        card = job_cards.nth(i)
        try:
            # --- Title + Link ---
            title_anchor = card.locator(".elementor-widget-theme-post-title a")
            if not title_anchor.count():
                title_anchor = card.locator("a").first()

            title = title_anchor.inner_text().strip()
            link = title_anchor.get_attribute("href") or ""

            # --- Date Posted ---
            time_el = card.locator(".elementor-post-info__item--type-date time")
            if time_el.count():
                raw_date = time_el.inner_text().strip()
            else:
                date_block = card.locator("xpath=.//*[contains(normalize-space(),'Published On')]//time")
                raw_date = date_block.inner_text().strip() if date_block.count() else ""

            parsed_date = parse_date(raw_date) if raw_date else ""

            # Location is always Nairobi for SIC jobs
            location = "Nairobi"

            jobs.append({
                "Title": title,
                "Location": location,
                "Link": link,
                "Date Published (parsed)": parsed_date,
                "Date Published (raw)": raw_date,
            })

            print(f"✅ {title} | {location} | {parsed_date or raw_date}")

        except PlaywrightTimeoutError:
            print(f"⚠️ Timeout reading job card {i}. Skipping.")
        except Exception as e:
            print(f"❌ Error parsing job card {i}: {e}")

    # Save CSV
    with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["Title", "Location", "Link", "Date Published (parsed)", "Date Published (raw)"],
        )
        writer.writeheader()
        writer.writerows(jobs)

    print(f"\n💾 Saved {len(jobs)} job(s) to {CSV_FILE}.")

    context.close()
    browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
