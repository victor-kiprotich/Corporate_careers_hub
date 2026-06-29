import os
import csv
import re
from playwright.sync_api import Playwright, sync_playwright


def write_jobs_to_csv(jobs, filename="kengen_jobs.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Section", "Job Title", "Job Link"])
        for section, title, link in jobs:
            writer.writerow([section, title, link])


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    print("🌐 Visiting KenGen Careers page...")
    page.goto("https://careers.kengen.co.ke/")

    all_jobs = []

    # ---------- CAREERS SECTION ----------
    print("\n🔎 Checking 'Careers' section...")
    page.get_by_role("link", name=re.compile("Careers")).click()

    try:
        page.wait_for_selector(".job-card a", timeout=5000)
        careers_jobs = page.locator(".job-card a")
        count = careers_jobs.count()
        for i in range(count):
            job = careers_jobs.nth(i)
            title = job.inner_text().strip()
            href = job.get_attribute("href")
            if href:
                all_jobs.append(("Careers", title, href))
    except:
        print("❌ No jobs found in 'Careers' section.")

    # ---------- INTERNSHIP SECTION ----------
    print("\n🔎 Checking 'Internship' section...")
    page.goto("https://careers.kengen.co.ke/")
    page.get_by_role("link", name=re.compile("Internship")).click()

    try:
        page.wait_for_selector(".job-card a", timeout=5000)
        internship_jobs = page.locator(".job-card a")
        count = internship_jobs.count()
        for i in range(count):
            job = internship_jobs.nth(i)
            title = job.inner_text().strip()
            href = job.get_attribute("href")
            if href:
                all_jobs.append(("Internship", title, href))
    except:
        print("❌ No jobs found in 'Internship' section.")

    # ---------- INDUSTRIAL ATTACHMENT SECTION ----------
    print("\n📄 Fetching 'Industrial Attachment' page link...")
    page.goto("https://careers.kengen.co.ke/")
    link_handle = page.get_by_role("link", name=re.compile("Industrial Attachment"))

    try:
        href = link_handle.get_attribute("href")
        if href:
            full_link = page.url if not href.startswith("http") else href
            all_jobs.append(("Industrial Attachment", "Industrial Attachment PDF", full_link))
            print(f"✅ Found: {full_link}")
        else:
            print("⚠️ Could not extract Industrial Attachment link.")
    except:
        print("❌ Failed to locate Industrial Attachment section.")

    # ---------- SAVE TO CSV ----------
    if all_jobs:
        write_jobs_to_csv(all_jobs)
        print(f"\n✅ Saved {len(all_jobs)} job(s) to kengen_jobs.csv")
    else:
        print("\n📭 No jobs found to save.")

    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
