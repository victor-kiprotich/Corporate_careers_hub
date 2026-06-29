from playwright.sync_api import sync_playwright, TimeoutError
import csv

def scrape_g4s_kenya_jobs():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            print("🌐 Navigating to G4S Kenya job listings...")
            page.goto("https://careers.g4s.com/en/search-jobs/Kenya/3072/2/192950/1/38/50/2", timeout=60000)

            # Wait for job cards to load
            page.wait_for_selector("a.job-list-tile__anchor", timeout=30000)
            job_cards = page.locator("a.job-list-tile__anchor")
            count = job_cards.count()

            if count == 0:
                print("❌ No jobs found in Kenya.")
                return

            print(f"✅ {count} jobs found.\n")
            jobs = []

            for i in range(count):
                try:
                    job = job_cards.nth(i)
                    job.click(timeout=10000)
                    page.wait_for_selector("h1", timeout=10000)

                    title = page.locator("h1").inner_text(timeout=5000)

                    # Extract location and category
                    location = page.locator("text=Location:").evaluate("el => el.nextSibling?.textContent || 'N/A'")
                    category = page.locator("text=Job Category:").evaluate("el => el.nextSibling?.textContent || 'N/A'")
                    apply_link = page.url

                    print(f"📄 {title.strip()}")

                    jobs.append({
                        "title": title.strip(),
                        "location": location.strip(),
                        "category": category.strip(),
                        "link": apply_link
                    })

                    page.go_back(timeout=10000)
                    page.wait_for_selector("a.job-list-tile__anchor", timeout=15000)

                except Exception as job_error:
                    print(f"⚠️ Error scraping job {i+1}: {job_error}")
                    page.go_back(timeout=10000)
                    page.wait_for_selector("a.job-list-tile__anchor", timeout=15000)

            # Save to CSV
            with open("g4s_kenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["title", "location", "category", "link"])
                writer.writeheader()
                writer.writerows(jobs)

            print(f"\n✅ Saved {len(jobs)} jobs to g4s_kenya_jobs.csv")

        except TimeoutError as te:
            print(f"⏰ Timeout error: {te}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        finally:
            context.close()
            browser.close()

# Run the scraper
scrape_g4s_kenya_jobs()
