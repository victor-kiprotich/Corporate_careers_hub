import asyncio
import re
import pandas as pd
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

SEARCH_URL = "https://i-pride.kenya-airways.com/OA_HTML/OA.jsp?page=/oracle/apps/irc/candidateSelfService/webui/VisJobSchPG&_ri=821&SeededSearchFlag=N&Contractor=Y&Employee=Y&OASF=IRC_VIS_JOB_SEARCH_PAGE&_ti=1516056481&oapc=3&OAMC=75477_25_0&menu=Y&oaMenuLevel=1&oas=mLXS-yH5QIK-nRbDgGEcdg"

async def run(playwright):
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()

    print("🔗 Opening Kenya Airways job board...")
    await page.goto(SEARCH_URL)
    await page.wait_for_load_state("networkidle")

    print("🌍 Selecting city: Nairobi, KE")
    await page.get_by_label("City Location").select_option("Nairobi,KE")
    await page.wait_for_load_state("networkidle")

    print("🔎 Running job search...")
    await page.get_by_role("button", name="Search", exact=True).click()
    await page.wait_for_load_state("networkidle")

    try:
        await page.wait_for_selector("table.xcg tbody tr", timeout=15000)
    except:
        print("❌ No job postings found.")
        await browser.close()
        return

    print("📥 Scraping job postings...")
    table_html = await page.locator("table.xcg").inner_html()
    soup = BeautifulSoup(table_html, "html.parser")
    tbody = soup.find("tbody")

    if not tbody:
        print("❌ No job table found.")
        await browser.close()
        return

    job_data = []
    for row in tbody.find_all("tr"):
        job_title = row.find("span", id=re.compile(r"JobSearchTable:JobTitle:\d+"))
        location = row.find("span", id=re.compile(r"JobSearchTable:LocationResult:\d+"))
        org_name = row.find("span", id=re.compile(r"JobSearchTable:OrganizationName:\d+"))
        posting_date = row.find("span", id=re.compile(r"JobSearchTable:DatePostedResult:\d+"))
        description_td = row.find_all("td")

        # Skip rows with missing job title
        if not job_title:
            continue

        job_data.append({
            "Job Title": job_title.get_text(strip=True),
            "Location": location.get_text(strip=True) if location else "N/A",
            "Organization Name": org_name.get_text(strip=True) if org_name else "N/A",
            "Job Description": description_td[5].get_text(strip=True) if len(description_td) > 5 else "N/A",
            "Posting Date": posting_date.get_text(strip=True) if posting_date else "N/A",
            "Apply Link": SEARCH_URL  # Generic job board link
        })

    if job_data:
        df = pd.DataFrame(job_data)
        df.to_csv("kenya_airways_jobs.csv", index=False, encoding="utf-8")
        print(f"✅ Found {len(job_data)} job postings.")
        print("📄 Saved to 'kenya_airways_jobs_async.csv'")
    else:
        print("❌ No valid job rows found.")

    await browser.close()

async def main():
    async with async_playwright() as playwright:
        await run(playwright)

if __name__ == "__main__":
    asyncio.run(main())
