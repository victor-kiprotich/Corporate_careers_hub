import asyncio
import csv
from playwright.async_api import async_playwright

async def scrape_krb_jobs():
    base_url = "https://krb-xjobs.brassring.com"
    search_url = f"{base_url}/TGnewUI/Search/Home/Home?partnerid=30025&siteid=5750#home"

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Navigating to job board...")
        await page.goto(search_url, timeout=60000)

        # Wait for location input and search
        await page.wait_for_selector("input[aria-label='location']", timeout=10000)
        location_input = await page.query_selector("input[aria-label='location']")
        await location_input.click()
        await location_input.fill("Kenya")
        await page.wait_for_timeout(1000)  # Let dropdown appear
        await page.keyboard.press("ArrowDown")
        await page.keyboard.press("Enter")

        await page.get_by_role("button", name="Search").click()
        await page.wait_for_timeout(5000)  # Let jobs load

        job_links = await page.query_selector_all("a.jobProperty.jobtitle")
        print(f"📦 Found {len(job_links)} job(s)")

        for i, job in enumerate(job_links):
            try:
                # ✅ FIXED: get_attribute from 'job', not 'job_links'
                job_href = await job.get_attribute("href")
                if not job_href:
                    continue

                full_link = job_href if job_href.startswith("http") else base_url + job_href

                detail_page = await context.new_page()
                await detail_page.goto(full_link, timeout=30000)

                await detail_page.wait_for_selector("h1.jobtitleInJobDetails", timeout=15000)
                title_el = await detail_page.query_selector("h1.jobtitleInJobDetails")
                job_title = await title_el.inner_text() if title_el else "N/A"

                detail_els = await detail_page.query_selector_all("p.section2RightfieldsInJobDetails")
                location = await detail_els[0].inner_text() if len(detail_els) > 0 else ""
                expiry_date = await detail_els[1].inner_text() if len(detail_els) > 1 else ""

                apply_link_el = await detail_page.query_selector("a[ng-click='handlers.applyClick($event)']")
                apply_href = await apply_link_el.get_attribute("href") if apply_link_el else full_link

                results.append({
                    "Title": job_title.strip(),
                    "Link": full_link.strip(),
                    "Location": location.strip(),
                    "Expiry Date": expiry_date.strip(),
                    "Apply Link": apply_href if apply_href and apply_href.startswith("http") else full_link
                })

                print(f"[{i+1}] ✅ {job_title.strip()}")
                await detail_page.close()

            except Exception as e:
                print(f"[{i+1}] ❌ Error: {e}")

        await browser.close()

    # Save results to CSV
    keys = ["Title", "Link", "Location", "Expiry Date", "Apply Link"]
    with open("krb_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Saved {len(results)} job(s) to krb_jobs.csv")

if __name__ == "__main__":
    asyncio.run(scrape_krb_jobs())
