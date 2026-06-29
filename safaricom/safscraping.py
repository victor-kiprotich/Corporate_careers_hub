import asyncio
import re
from bs4 import BeautifulSoup
import pandas as pd
from playwright.async_api import Playwright, async_playwright
from urllib.parse import urljoin


async def run(playwright: Playwright) -> None:
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()

    base_url = "https://egjd.fa.us6.oraclecloud.com"
    jobs_url = f"{base_url}/hcmUI/CandidateExperience/en/sites/CX/jobs"

    await page.goto(jobs_url)
    await page.wait_for_load_state("load")

    print("🔗 Collecting job URLs...")

    await page.wait_for_selector("a.job-grid-item__link")
    job_cards = await page.locator("a.job-grid-item__link").all()

    job_urls = [await card.get_attribute("href") for card in job_cards]
    job_urls = [urljoin(base_url, url) for url in job_urls if url]

    print(f"✅ Found {len(job_urls)} job postings.\n")

    job_data = []

    for i, job_url in enumerate(job_urls):
        print(f"🔎 Scraping job {i+1} of {len(job_urls)}")

        try:
            job_page = await context.new_page()
            await job_page.goto(job_url)
            await job_page.wait_for_selector("h1.heading.job-details__title")

            # Job Title
            job_title = await job_page.locator("h1.heading.job-details__title").inner_text()

            # Job Description
            try:
                description_html = await job_page.locator("div[data-bind='html: pageData().job.description']").inner_html()
                soup = BeautifulSoup(description_html, 'html.parser')

                # Format paragraphs and lists
                from bs4.element import NavigableString
                for br in soup.find_all("br"):
                    br.replace_with(NavigableString("\n"))

                for li in soup.find_all("li"):
                    li.insert_before("\n• ")

                description_text = soup.get_text(separator="\n", strip=True)
                description_text = re.sub(r'\n+', '\n', description_text).strip()
                # sanitize description
                description_text = re.sub(r'\s+', ' ', description_text)
            except:
                description_text = "No description found"

            # Append job data (link goes to job card)
            job_data.append({
                "Job Title": job_title,
                "Job Description": description_text,
                "Job Link": job_url
            })

            await job_page.close()

        except Exception as e:
            print(f"❌ Error scraping job at {job_url}: {e}")

    # Save to CSV
    df = pd.DataFrame(job_data)
    df.to_csv("safaricom_jobs.csv", index=False, encoding="utf-8", lineterminator="\n")
    print("\n📄 Job data saved to 'job_details.csv'.")


async def main() -> None:
    async with async_playwright() as playwright:
        await run(playwright)


if __name__ == "__main__":
    asyncio.run(main())
