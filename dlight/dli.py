import asyncio
import csv
from playwright.async_api import async_playwright

OUTPUT_FILE = "dlight_jobs.csv"

async def scrape_dlight_jobs():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌐 Opening d.light Careers page...")
        await page.goto("https://dlight.zohorecruit.in/jobs/Careers", timeout=120_000)

        # Click "View Openings"
        await page.get_by_role("link", name="View Openings").click()

        # Wait for input box and type "Kenya"
        input_box = page.get_by_role("textbox", name="City, state/province or")
        await input_box.fill("Kenya")
        await page.get_by_role("button", name="Search").click()

        await page.wait_for_timeout(5000)

        job_cards = await page.locator("div.cw-filter-joblist-left").all()
        print(f"🔍 Found {len(job_cards)} Kenya job(s).")

        results = []

        for i, card in enumerate(job_cards):
            try:
                # Title and Link
                link_el = card.locator("a.cw-3-title")
                title = await link_el.text_content() or "N/A"
                relative_link = await link_el.get_attribute("href")
                full_link = relative_link if relative_link.startswith("http") else f"https://dlight.zohorecruit.in{relative_link}"

                # Location and Experience
                subhead = card.locator("p.filter-subhead")
                location_text = await subhead.text_content() or ""
                location = location_text.split("\n")[0].strip()

                # Extract experience separately
                exp_tags = card.locator("span.search-work-experience")
                exp_count = await exp_tags.count()
                experience = await exp_tags.nth(exp_count - 1).text_content() if exp_count > 0 else "N/A"

                # Open job page to get description
                job_page = await context.new_page()
                await job_page.goto(full_link, timeout=60000)
                await job_page.wait_for_timeout(2000)

                description = "N/A"
                paragraphs = job_page.locator("div#jobdesc p")
                para_count = await paragraphs.count()
                for j in range(para_count):
                    text = await paragraphs.nth(j).text_content()
                    if text and len(text.strip()) > 20:
                        description = text.strip()
                        break

                await job_page.close()

                results.append({
                    "Job Title": title.strip(),
                    "Location": location,
                    "Experience": experience.strip(),
                    "Apply Link": full_link
                })

                print(f"✅ {title.strip()} | {location} | {experience.strip()}")

            except Exception as e:
                print(f"⚠️ Skipped a job due to error: {e}")
                continue

        # Save to CSV
        with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Job Title", "Location", "Experience", "Apply Link", "Description"])
            writer.writeheader()
            writer.writerows(results)

        print(f"\n📁 Saved {len(results)} jobs to {OUTPUT_FILE}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_dlight_jobs())
