from playwright.sync_api import sync_playwright, TimeoutError
import csv
import time

def scrape_g4s_kenya_jobs():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            print("🌐 Navigating to G4S Kenya job listings...")
            page.goto("https://careers.g4s.com/en/search-jobs/Kenya/3072/2/192950/1/38/50/2", timeout=60000)

            # Wait for job cards
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
                    job.scroll_into_view_if_needed(timeout=5000)

                    try:
                        job.click(timeout=10000)
                    except:
                        # Retry clicking after scroll wait
                        time.sleep(2)
                        job.click(timeout=10000)

                    page.wait_for_selector("h1", timeout=10000)
                    title = page.locator("h1").inner_text(timeout=5000)

                    # Grab all strong labels and values next to them
                    details = page.locator("div.job-detail-metadata-row")
                    location = category = "N/A"

                    for j in range(details.count()):
                        label = details.nth(j).locator("strong").inner_text().strip()
                        value = details.nth(j).locator("span").inner_text().strip()
                        if label.lower().startswith("location"):
                            location = value
                        elif label.lower().startswith("job category"):
                            category = value

                    apply_link = page.url
                    print(f"📄 {title.strip()}")

                    jobs.append({
                        "title": title.strip(),
                        "location": location,
                        "category": category,
                        "link": apply_link
                    })

                    # Go back and wait longer
                    page.go_back(timeout=15000)
                    page.wait_for_selector("a.job-list-tile__anchor", timeout=30000)

                except Exception as job_error:
                    print(f"⚠️ Error scraping job {i+1}: {job_error}")
                    try:
                        page.go_back(timeout=15000)
                        page.wait_for_selector("a.job-list-tile__anchor", timeout=30000)
                    except:
                        print("🔁 Reloading job list page...")
                        page.goto("https://careers.g4s.com/en/search-jobs/Kenya/3072/2/192950/1/38/50/2", timeout=60000)
                        page.wait_for_selector("a.job-list-tile__anchor", timeout=30000)

            # Save results
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

# Run
scrape_g4s_kenya_jobs()
