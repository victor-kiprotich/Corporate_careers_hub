import asyncio
import csv
from playwright.async_api import async_playwright, TimeoutError

async def handle_captcha_if_present(page):
    try:
        captcha_frame = await page.wait_for_selector("iframe[src*='recaptcha']", timeout=5000)
        frame = await captcha_frame.content_frame()
        checkbox = await frame.wait_for_selector("#recaptcha-anchor", timeout=5000)
        await checkbox.click()
        print("🤖 CAPTCHA checkbox clicked. Waiting to solve...")
        await page.wait_for_selector("h1.wd-entities-title.title", timeout=60000)
    except TimeoutError:
        print("ℹ️ No CAPTCHA detected, continuing...")

async def scrape_kaa_jobs():
    base_url = "https://www.kaa.go.ke"
    jobs_url = f"{base_url}/jobs/?v=25bc6654798e"
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌍 Navigating to KAA jobs page...")
        await page.goto(jobs_url, timeout=60000)

        await page.wait_for_selector("h4 a span.job-title", timeout=30000)
        job_links = await page.query_selector_all("h4 a")

        print(f"📦 Found {len(job_links)} job(s)")

        for i, link in enumerate(job_links):
            try:
                href = await link.get_attribute("href")
                full_link = href if href.startswith("http") else f"{base_url}{href}"

                detail_page = await context.new_page()

                try:
                    await detail_page.goto(full_link, timeout=60000)
                except TimeoutError:
                    print(f"[{i+1}] ❌ Page load failed: {full_link}")
                    await detail_page.close()
                    continue

                await handle_captcha_if_present(detail_page)

                try:
                    await detail_page.wait_for_selector("h1.wd-entities-title.title", timeout=20000)
                    title_el = await detail_page.query_selector("h1.wd-entities-title.title")
                except TimeoutError:
                    print(f"[{i+1}] ❌ Title selector not found: {full_link}")
                    await detail_page.close()
                    continue

                job_title = await title_el.inner_text() if title_el else "N/A"

                date_el = await detail_page.query_selector("div.job-date")
                date_posted = await date_el.inner_text() if date_el else "N/A"

                desc_el = await detail_page.query_selector("div.job-description")
                description = await desc_el.inner_text() if desc_el else "N/A"

                results.append({
                    "Title": job_title.strip(),
                    "Link": full_link.strip(),
                    "Date Posted": date_posted.replace("Posted", "").strip(),
                    "Description": description.strip()
                })

                print(f"[{i+1}] ✅ {job_title.strip()}")
                await detail_page.close()

            except Exception as e:
                print(f"[{i+1}] ❌ Error: {e}")

        await browser.close()

    # Save to CSV
    keys = ["Title", "Link", "Date Posted", "Description"]
    with open("kaa_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Saved {len(results)} job(s) to kaa_jobs.csv")

if __name__ == "__main__":
    asyncio.run(scrape_kaa_jobs())
