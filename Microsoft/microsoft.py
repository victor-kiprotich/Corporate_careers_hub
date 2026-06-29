import asyncio
import csv
from playwright.async_api import async_playwright

OUTPUT_FILE = "microsoft_kenya_jobs.csv"
START_URL = "https://jobs.careers.microsoft.com/global/en/search?lc=Kenya"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(START_URL, timeout=60000)
        print("🔍 Visiting Microsoft Kenya Careers Page...")

        # Wait for job cards
        try:
            await page.wait_for_selector("div.jobs-list-item", timeout=15000)
        except:
            print("❌ No jobs available or site structure changed.")
            await browser.close()
            return

        job_cards = await page.locator("div.jobs-list-item").all()
        if not job_cards:
            print("❌ No job cards found on page.")
            await browser.close()
            return

        jobs = []
        for card in job_cards:
            title_el = card.locator("h3.job-title")
            location_el = card.locator("span.job-location")
            link_el = card.locator("a.job-title-link")

            title = (await title_el.text_content() or "").strip()
            location = (await location_el.text_content() or "").strip()
            href = await link_el.get_attribute("href") or ""
            link = f"https://jobs.careers.microsoft.com{href}"

            print(f"📝 {title} | {location}")

            # Go to detail page to extract description
            job_page = await context.new_page()
            await job_page.goto(link, timeout=60000)

            try:
                await job_page.wait_for_selector("div.job-description p", timeout=10000)
                description = await job_page.locator("div.job-description p").first.text_content()
            except:
                description = "No description available."

            await job_page.close()

            jobs.append({
                "Job Title": title,
                "Location": location,
                "Description": description.strip(),
                "Apply Link": link
            })

        # Save to CSV
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Job Title", "Location", "Description", "Apply Link"])
            writer.writeheader()
            writer.writerows(jobs)

        print(f"✅ Done! Saved {len(jobs)} job(s) to {OUTPUT_FILE}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
