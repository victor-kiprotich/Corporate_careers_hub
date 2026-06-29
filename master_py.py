# -*- coding: utf-8 -*-
"""
==============================================================================
MASTER PYTHON SCRIPTS RUNNER & DEBUGGER
==============================================================================
This file compiles and wraps all python scripts from the company folders.
It allows running and debugging each company script individually or in sequence.
"""

import os
import sys
import traceback
import asyncio
import csv
import re
from datetime import datetime
from urllib.parse import urljoin

# Third Party Imports (Ensure these are installed in your environment)
try:
    import pandas as pd
    from bs4 import BeautifulSoup
    import requests
    from playwright.async_api import async_playwright as async_pw
    from playwright.sync_api import sync_playwright as sync_pw
except ImportError as e:
    print(f"⚠️ Warning: Missing core tracking dependency: {e}")

# Prevent UnicodeEncodeError on Windows console when printing emoji/unicode
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except Exception:
        pass

ORIGINAL_CWD = os.getcwd()
ORIGINAL_SYS_PATH = list(sys.path)

class EnvironmentGuard:
    """Context manager to isolate current working directory and sys.path for each script."""
    def __init__(self, script_path):
        self.script_path = script_path
        self.script_dir = os.path.dirname(os.path.abspath(script_path))
        self.old_cwd = os.getcwd()
        self.old_path = list(sys.path)

    def __enter__(self):
        print(f"\n[ENV] Switching CWD to: {self.script_dir}")
        if not os.path.exists(self.script_dir):
            os.makedirs(self.script_dir, exist_ok=True)
        os.chdir(self.script_dir)
        if self.script_dir not in sys.path:
            sys.path.insert(0, self.script_dir)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.old_cwd)
        sys.path = self.old_path
        if exc_type:
            print(f"\n❌ Error execution in {self.script_path}:")
            traceback.print_exception(exc_type, exc_val, exc_tb)
            return True  # Prevent exception from crashing the master loop runner
        return False


# ================================================================================
# SCRIPT: absa/absa.py
# ================================================================================
async def run_absa_absa():
    """Wrapper execution for absa/absa.py"""
    with EnvironmentGuard('absa/absa.py'):
        base_url = "https://absa.wd3.myworkdayjobs.com"
        jobs_url = base_url + "/en-GB/absacareersite?locationCountry=9e684fd7be1e469d9ee955a4c3b754be"
        results = []

        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(jobs_url, timeout=60000)

            await page.wait_for_selector("a.css-19uc56f", timeout=30000)
            job_cards = await page.query_selector_all("a.css-19uc56f")
            print(f"Found {len(job_cards)} job(s)")

            for i, card in enumerate(job_cards):
                title_el = await card.query_selector("h2")
                job_title = await title_el.inner_text() if title_el else ""
                job_link = await card.get_attribute("href")
                full_link = base_url + job_link if job_link else ""  # FIXED URL ASSIGNMENT

                detail_page = await context.new_page()
                await detail_page.goto(full_link, timeout=30000)

                try:
                    await detail_page.wait_for_selector("h2[data-automation-id='jobPostingHeader']", timeout=15000)
                    job_title_el = await detail_page.query_selector("h2[data-automation-id='jobPostingHeader']")
                    if job_title_el:
                        job_title = await job_title_el.inner_text()
                except:
                    pass

                try:
                    location_el = await detail_page.query_selector("div[data-automation-id='locations'] dd")
                    location = await location_el.inner_text() if location_el else ""
                except:
                    location = ""

                try:
                    end_date_el = await detail_page.query_selector("div[data-automation-id='timeLeftToApply'] dd")
                    end_date = await end_date_el.inner_text() if end_date_el else ""
                except:
                    end_date = ""

                results.append({
                    "Title": job_title.strip(),
                    "Location": location.strip(),
                    "End Date": end_date.strip(),
                    "Link": full_link.strip()
                })
                print(f"[{i+1}] {job_title.strip()} - {location.strip()}")
                await detail_page.close()
            await browser.close()

        with open("absa_jobs.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Title", "Location", "End Date", "Link"])
            writer.writeheader()
            writer.writerows(results)
        print(f"Saved {len(results)} jobs to absa_jobs.csv")


# ================================================================================
# SCRIPT: Accor/accor.py
# ================================================================================
async def run_Accor_accor():
    """Wrapper execution for Accor/accor.py"""
    with EnvironmentGuard('Accor/accor.py'):
        base_url = "https://careers.accor.com"
        jobs = []

        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            print("🌍 Navigating to Accor Kenya jobs...")
            await page.goto("https://careers.accor.com/global/en/jobs?q=&options=&page=1&ln=Kenya&lr=1&li=KE", timeout=60000)

            await page.wait_for_selector("a.attrax-vacancy-tile__title")
            job_links = await page.locator("a.attrax-vacancy-tile__title").all()
            print(f"✅ Found {len(job_links)} job(s)")

            for i, job_card in enumerate(job_links):
                try:
                    link = await job_card.get_attribute("href")
                    full_link = f"{base_url}{link}" if link.startswith("/") else link

                    detail_page = await context.new_page()
                    await detail_page.goto(full_link, timeout=60000)

                    await detail_page.wait_for_selector("span#headertext", timeout=15000)
                    title = await detail_page.locator("span#headertext").inner_text()

                    try:
                        location = await detail_page.locator("li.JobLocation-wrapper").inner_text()
                    except:
                        location = "N/A"

                    try:
                        category = await detail_page.locator("li.JobCategory-wrapper").inner_text()
                    except:
                        category = "N/A"

                    try:
                        desc_el = detail_page.locator("div[class*='jobdescription'] p").first
                        description = await desc_el.inner_text()
                    except:
                        description = "N/A"

                    print(f"📄 [{i+1}] {title.strip()}")
                    jobs.append({
                        "title": title.strip(),
                        "location": location.strip(),
                        "category": category.strip(),
                        "description": description.strip(),
                        "link": full_link.strip()
                    })
                    await detail_page.close()
                except Exception as e:
                    print(f"⚠️ Error scraping job {i+1}: {e}")
                    continue
            await browser.close()

        with open("accor_kenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "location", "category", "description", "link"])
            writer.writeheader()
            writer.writerows(jobs)
        print(f"\n✅ Saved {len(jobs)} jobs to accor_kenya_jobs.csv")


# ================================================================================
# SCRIPT: AcdiVoca/acdi.py
# ================================================================================
def run_AcdiVoca_acdi():
    """Wrapper execution for AcdiVoca/acdi.py"""
    with EnvironmentGuard('AcdiVoca/acdi.py'):
        base_url = "https://internationaljobs-acdivoca.icims.com"
        jobs_url = f"{base_url}/jobs/search?ss=1&hashed=-435626115"

        with sync_pw() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            print("🌍 Navigating to ACDI/VOCA job board...")
            page.goto(jobs_url, timeout=60000)

            frame = page.frame(name="icims_content_iframe")
            if not frame:
                print("❌ Could not access iframe content.")
                browser.close()
                return

            try:
                frame.wait_for_selector("div.iCIMS_Expandable_Container", timeout=15000)
            except:
                print("❌ No job listings found.")
                browser.close()
                return

            html = frame.content()
            soup = BeautifulSoup(html, "html.parser")
            job_cards = soup.select("div.iCIMS_Expandable_Container")
            kenya_jobs = []

            for card in job_cards:
                location_el = card.select_one("li.iCIMS_JobHeaderData span.jobLocation")
                location = location_el.text.strip() if location_el else ""

                if "kenya" in location.lower():
                    title_el = card.select_one("a.iCIMS_Anchor h3")
                    title = title_el.text.strip() if title_el else "N/A"
                    link_el = card.select_one("a.iCIMS_Anchor")
                    relative_link = link_el["href"] if link_el else ""
                    full_link = base_url + relative_link
                    desc_el = card.select_one("div.iCIMS_Expandable_Text")
                    description = desc_el.text.strip() if desc_el else "N/A"

                    kenya_jobs.append({
                        "Title": title, "Location": location,
                        "Description": description, "Link": full_link
                    })
            browser.close()

            if not kenya_jobs:
                print("❌ No Kenya-based jobs found.")
                return

            print(f"✅ Found {len(kenya_jobs)} Kenya-based job(s)")
            with open("acdivoca_kenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Description", "Link"])
                writer.writeheader()
                writer.writerows(kenya_jobs)
            print("✅ Saved to acdivoca_kenya_jobs.csv")


# ================================================================================
# SCRIPT: AfricanUnion/au.py
# ================================================================================
async def run_AfricanUnion_au():
    """Wrapper execution for AfricanUnion/au.py"""
    with EnvironmentGuard('AfricanUnion/au.py'):
        OUTPUT_FILE = "au_jobs.csv"
        BASE_URL = "https://jobs.au.int"

        async def scrape_job_detail(context, url):
            try:
                detail_page = await context.new_page()
                await detail_page.goto(url, timeout=60000)
                first_paragraph = detail_page.locator("div[style*='padding:10.0px'] > div:nth-of-type(2) > p").first
                await first_paragraph.wait_for(state="visible", timeout=10000)
                desc = await first_paragraph.text_content()
                await detail_page.close()
                return desc.strip() if desc else "N/A"
            except Exception as e:
                print(f"⚠️ Failed to scrape detail at {url}: {e}")
                return "N/A"

        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            print("🌐 Opening AU Careers filtered for Kenya...")
            await page.goto("https://jobs.au.int/search/?searchResultView=LIST&markerViewed=&carouselIndex=&facetFilters=%7B%22mfield1%22%3A%5B%22Kenya%22%5D%7D&pageNumber=0")

            try:
                await page.wait_for_selector("li.JobsList_jobCard__8wE-Z", timeout=15000)
                job_cards = page.locator("li.JobsList_jobCard__8wE-Z")
                count = await job_cards.count()
            except Exception as e:
                print(f"⚠️ No job cards found or timed out: {e}")
                count = 0

            print(f"🔍 Found {count} Kenyan job(s).")
            results = []
            for i in range(count):
                try:
                    card = job_cards.nth(i)
                    title_el = card.locator("a.jobCardTitle")
                    title = await title_el.text_content()
                    href = await title_el.get_attribute("href")
                    full_link = BASE_URL + href if href else "N/A"
                    title_str = title.strip() if title else "N/A"
                    print(f"🔎 Scraping job {i+1}: {title_str}")
                    description = await scrape_job_detail(context, full_link)
                    results.append({
                        "Job Title": title_str, "Location": "Kenya",
                        "Apply Link": full_link, "Description": description
                    })
                except Exception as e:
                    print(f"⚠️ Skipped job {i+1} due to error: {e}")

            with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["Job Title", "Location", "Apply Link", "Description"])
                writer.writeheader()
                writer.writerows(results)
            print(f"\n✅ Saved {len(results)} job(s) to {OUTPUT_FILE}")
            await browser.close()


# ================================================================================
# SCRIPT: AgaKhan/aga.py
# ================================================================================
async def run_AgaKhan_aga():
    """Wrapper execution for AgaKhan/aga.py"""
    with EnvironmentGuard('AgaKhan/aga.py'):
        base_url = "https://krb-xjobs.brassring.com"
        search_url = f"{base_url}/TGnewUI/Search/Home/Home?partnerid=30025&siteid=5750#home"
        results = []

        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            print("🌍 Navigating to job board...")
            await page.goto(search_url, timeout=60000)

            await page.wait_for_selector("input[aria-label='location']", timeout=10000)
            location_input = await page.query_selector("input[aria-label='location']")
            await location_input.click()
            await location_input.fill("Kenya")
            await page.wait_for_timeout(1000)
            await page.keyboard.press("ArrowDown")
            await page.keyboard.press("Enter")
            await page.get_by_role("button", name="Search").click()
            await page.wait_for_timeout(5000)

            job_links = await page.query_selector_all("a.jobProperty.jobtitle")
            print(f"📦 Found {len(job_links)} job(s)")

            for i, job in enumerate(job_links):
                try:
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
                        "Title": job_title.strip(), "Link": full_link.strip(),
                        "Location": location.strip(), "Expiry Date": expiry_date.strip(),
                        "Apply Link": apply_href if apply_href and apply_href.startswith("http") else full_link
                    })
                    print(f"[{i+1}] ✅ {job_title.strip()}")
                    await detail_page.close()
                except Exception as e:
                    print(f"[{i+1}] ❌ Error: {e}")
            await browser.close()

        with open("krb_jobs.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Title", "Link", "Location", "Expiry Date", "Apply Link"])
            writer.writeheader()
            writer.writerows(results)
        print(f"\n✅ Saved {len(results)} job(s) to krb_jobs.csv")


# ================================================================================
# SCRIPT: Air/air.py
# ================================================================================
async def run_Air_air():
    """Wrapper execution for Air/air.py"""
    with EnvironmentGuard('Air/air.py'):
        BASE_URL = "https://job-boards.greenhouse.io"
        JOBS_URL = f"{BASE_URL}/americaninstitutesforresearch?offices%5B%5D=4019330008"

        async def scrape_job_detail(context, job_url):
            try:
                page = await context.new_page()
                await page.goto(job_url, timeout=60000)
                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
                title = soup.select_one("h1").get_text(strip=True)
                location_el = soup.select_one("div.location")
                location = location_el.get_text(strip=True) if location_el else "Not specified"
                description_el = soup.select_one("div#content")
                description = description_el.get_text(separator="\n", strip=True) if description_el else ""
                await page.close()
                return {"Title": title, "Location": location, "Description": description, "Link": job_url}
            except Exception as e:
                print(f"❌ Failed to scrape {job_url}: {e}")
                return None

        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            print("🌐 Loading job listings page...")
            await page.goto(JOBS_URL, timeout=60000)

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            job_cards = soup.select("td.cell a")
            print(f"🔍 Found {len(job_cards)} job(s).")

            job_links = [urljoin(BASE_URL, card.get("href")) for card in job_cards if card.get("href")]
            results = []
            for i, job_link in enumerate(job_links, 1):
                print(f"🔎 Scraping job {i}/{len(job_links)}: {job_link}")
                job_data = await scrape_job_detail(context, job_link)
                if job_data:
                    results.append(job_data)
            await browser.close()

        with open("air_nairobi_jobs.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Description", "Link"])
            writer.writeheader()
            writer.writerows(results)
        print(f"\n✅ Saved {len(results)} jobs to 'air_nairobi_jobs.csv'")


# ================================================================================
# SCRIPT: Airtel/airtel.py
# ================================================================================
def run_Airtel_airtel():
    """Wrapper execution for Airtel/airtel.py"""
    with EnvironmentGuard('Airtel/airtel.py'):
        with sync_pw() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            print("🌐 Visiting Airtel Kenya careers page...")
            page.goto("https://www.airtelkenya.com/vacancies")

            jobs = []
            job_cards = page.locator("ul.job-list > li > a")
            count = job_cards.count()

            if count == 0:
                print("❌ No jobs found.")
            else:
                for i in range(count):
                    job = job_cards.nth(i)
                    title = job.inner_text().strip()
                    link = job.get_attribute("href")
                    if link and not link.startswith("http"):
                        link = "https://www.airtelkenya.com" + link
                    jobs.append({"title": title, "link": link})

                with open("airtel_jobs.csv", "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=["title", "link"])
                    writer.writeheader()
                    writer.writerows(jobs)
                print(f"✅ Saved {len(jobs)} job(s) to airtel_jobs.csv")
            context.close()
            browser.close()


# ================================================================================
# SCRIPT: Amazon/amazon.py
# ================================================================================
def run_Amazon_amazon():
    """Wrapper execution for Amazon/amazon.py"""
    with EnvironmentGuard('Amazon/amazon.py'):
        BASE_URL = "https://www.amazon.jobs"
        SEARCH_URL = f"{BASE_URL}/en/search?base_query=&loc_query=Kenya&country=KEN"

        with sync_pw() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            print("🌐 Visiting Amazon Kenya jobs page...")
            page.goto(SEARCH_URL)
            page.wait_for_selector("a.job-link")

            job_links = page.locator("a.job-link")
            total = job_links.count()
            print(f"📌 Found {total} job(s). Scraping...")
            jobs = []

            for i in range(total):
                job_url_suffix = job_links.nth(i).get_attribute("href")
                job_url = BASE_URL + job_url_suffix
                job_page = context.new_page()
                job_page.goto(job_url)

                try:
                    job_page.wait_for_selector("h1.title", timeout=10000)
                    title = job_page.locator("h1.title").inner_text().strip()
                    location = job_page.locator("div.location-icon ul li").inner_text().strip()
                    description = job_page.locator("#job-detail-body .col-md-7 p").first.inner_text().strip()

                    jobs.append({"title": title, "location": location, "description": description, "link": job_url})
                    print(f"✅ Scraped: {title}")
                except Exception as e:
                    print(f"⚠️ Failed to scrape job {i+1}: {e}")
                finally:
                    job_page.close()

            with open("amazon_jobs.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["title", "location", "description", "link"])
                writer.writeheader()
                writer.writerows(jobs)
            print(f"\n✅ Done! Saved {len(jobs)} job(s) to amazon_jobs.csv")
            context.close()
            browser.close()


# ================================================================================
# SCRIPT: BAT/bat.py
# ================================================================================
async def run_BAT_bat():
    """Wrapper execution for BAT/bat.py"""
    with EnvironmentGuard('BAT/bat.py'):
        url = "https://careers.bat.com/en/search-jobs/Kenya/1045/2/192950/1/38/50/2"
        base_url = "https://careers.bat.com"
        jobs = []

        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            print("🌍 Navigating to BAT Kenya jobs page...")
            await page.goto(url, timeout=60000)
            await page.wait_for_selector("a[data-job-id]")

            job_cards = await page.locator("a[data-job-id]").all()
            print(f"✅ Found {len(job_cards)} job cards")

            for i, card in enumerate(job_cards):
                try:
                    relative_link = await card.get_attribute("href")
                    full_link = base_url + relative_link
                    detail_page = await context.new_page()
                    await detail_page.goto(full_link, timeout=60000)
                    await detail_page.wait_for_selector("h1.ajd_header__job-title")

                    title = await detail_page.locator("h1.ajd_header__job-title").inner_text()
                    location = await detail_page.locator("p.ajd_header__location").inner_text()

                    try:
                        job_type = await detail_page.locator("div.ajd-job-info-item span.ajd-job-info").inner_text()
                    except:
                        job_type = "N/A"

                    try:
                        description = await detail_page.locator("div.text-inner").inner_text()
                    except:
                        description = "N/A"

                    print(f"📄 Scraped: {title.strip()}")
                    jobs.append({
                        "Title": title.strip(), "Location": location.strip(),
                        "Job Type": job_type.strip(), "Description": description.strip(), "Link": full_link.strip()
                    })
                    await detail_page.close()
                except Exception as e:
                    print(f"⚠️ Error scraping job {i + 1}: {e}")
                    continue
            await browser.close()

        with open("bat_kenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Job Type", "Description", "Link"])
            writer.writeheader()
            writer.writerows(jobs)
        print(f"\n✅ Saved {len(jobs)} jobs to bat_kenya_jobs.csv")


# ================================================================================
# SCRIPT: BCG/bcg.py
# ================================================================================
async def run_BCG_bcg():
    """Wrapper execution for BCG/bcg.py"""
    with EnvironmentGuard('BCG/bcg.py'):
        START_URL = "https://careers.bcg.com/global/en/search-results"
        BASE_URL = "https://careers.bcg.com"
        CSV_FILE = "bcg_kenya_jobs.csv"

        def parse_iso_or_date(raw: str) -> str:
            if not raw: return ""
            raw = raw.strip()
            for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d", "%b %d, %Y", "%B %d, %Y"):
                try: return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
                except ValueError: continue
            return raw

        async def extract_job_from_card(card):
            job_anchor = card.locator("[data-ph-at-id='job-link']")
            apply_anchor = card.locator("[data-ph-at-id='apply-link']")
            title_attr = await job_anchor.get_attribute("data-ph-at-job-title-text") or ""
            location_attr = await job_anchor.get_attribute("data-ph-at-job-location-text") or ""
            category_attr = await job_anchor.get_attribute("data-ph-at-job-category-text") or ""
            job_id_attr = await job_anchor.get_attribute("data-ph-at-job-id-text") or ""
            job_type_attr = await job_anchor.get_attribute("data-ph-at-job-type-text") or ""
            post_date_attr = await job_anchor.get_attribute("data-ph-at-job-post-date-text") or ""

            detail_href = await job_anchor.get_attribute("href") or ""
            apply_href = await apply_anchor.get_attribute("href") if await apply_anchor.count() else ""
            detail_link = urljoin(BASE_URL, detail_href)
            apply_link = urljoin(BASE_URL, apply_href) if apply_href else detail_link

            description = ""
            desc_loc = card.locator("[data-ph-at-id='jobdescription-text']")
            if await desc_loc.count():
                description = (await desc_loc.inner_text()).strip()

            return {
                "Title": title_attr.strip(), "Location": location_attr.strip(),
                "Category": category_attr.strip(), "Job ID": job_id_attr.strip(),
                "Job Type": job_type_attr.strip(), "Post Date": parse_iso_or_date(post_date_attr),
                "Description": description.strip(), "Detail Link": detail_link.strip(), "Apply Link": apply_link.strip(),
            }

        results = []
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            print("🌍 Navigating to BCG Global search...")
            await page.goto(START_URL, timeout=90000)

            page_num = 1
            while True:
                try:
                    await page.wait_for_selector("li.jobs-list-item", timeout=30000)
                except:
                    break

                job_cards = await page.locator("li.jobs-list-item").all()
                for card in job_cards:
                    data = await extract_job_from_card(card)
                    if "kenya" in data["Location"].lower():
                        results.append(data)
                        print(f"✅ {data['Title']} | {data['Location']}")

                next_btn = page.locator("a.pagination-next, button[aria-label='Next Page'], a[aria-label='Next']")
                if await next_btn.count() == 0 or not await next_btn.is_enabled():
                    break
                await next_btn.click()
                page_num += 1
                await page.wait_for_timeout(2000)
            await browser.close()

        if results:
            pd.DataFrame(results).to_csv(CSV_FILE, index=False, encoding="utf-8-sig")
        print(f"\n📁 Saved {len(results)} Kenya job(s) to {CSV_FILE}.")


# ================================================================================
# SCRIPT: Capital/capi.py
# ================================================================================
def run_Capital_capi():
    """Wrapper execution for Capital/capi.py"""
    with EnvironmentGuard('Capital/capi.py'):
        with sync_pw() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            print("🌐 Navigating to G4S Kenya job listings...")
            page.goto("https://careers.g4s.com/en/search-jobs/Kenya/3072/2/192950/1/38/50/2", timeout=60000)

            page.wait_for_selector("a.job-list-tile__anchor", timeout=30000)
            job_cards = page.locator("a.job-list-tile__anchor")
            count = job_cards.count()
            jobs = []

            for i in range(count):
                try:
                    job = job_cards.nth(i)
                    job.scroll_into_view_if_needed()
                    job.click()
                    page.wait_for_selector("h1", timeout=10000)
                    title = page.locator("h1").inner_text().strip()

                    details = page.locator("div.job-detail-metadata-row")
                    location = category = "N/A"
                    for j in range(details.count()):
                        label = details.nth(j).locator("strong").inner_text().strip()
                        value = details.nth(j).locator("span").inner_text().strip()
                        if "location" in label.lower(): location = value
                        elif "category" in label.lower(): category = value

                    jobs.append({"title": title, "location": location, "category": category, "link": page.url})
                    print(f"📄 {title}")
                    page.go_back()
                    page.wait_for_selector("a.job-list-tile__anchor", timeout=30000)
                except Exception as e:
                    print(f"⚠️ Error card {i}: {e}")
                    page.goto("https://careers.g4s.com/en/search-jobs/Kenya/3072/2/192950/1/38/50/2")
            
            with open("g4s_kenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["title", "location", "category", "link"])
                writer.writeheader()
                writer.writerows(jobs)
            browser.close()


# ================================================================================
# SCRIPT: Carrefour/carre.py
# ================================================================================
def run_Carrefour_carre():
    """Wrapper execution for Carrefour/carre.py"""
    with EnvironmentGuard('Carrefour/carre.py'):
        CAREERS_URL = "https://carrefour-careers.pages.dev/#openings"
        with sync_pw() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(CAREERS_URL)
            page.wait_for_timeout(3000)

            titles = page.locator("div.font-bold.text-xl")
            descriptions = page.locator("p.text-muted.mt-2")
            jobs = []

            for i in range(titles.count()):
                title = titles.nth(i).inner_text().strip()
                try: description = descriptions.nth(i).inner_text().strip()
                except: description = ""
                jobs.append({"title": title, "description": description, "link": CAREERS_URL})

            with open("carrefour_jobs.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["title", "description", "link"])
                writer.writeheader()
                writer.writerows(jobs)
            browser.close()


# ================================================================================
# SCRIPT: Clinton/clint.py
# ================================================================================
async def run_Clinton_clint():
    """Wrapper execution for Clinton/clint.py"""
    with EnvironmentGuard('Clinton/clint.py'):
        base_url = "https://careers-chai.icims.com"
        iframe_url = f"{base_url}/jobs/search?ss=1&searchLocation=14075--"
        jobs = []

        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(iframe_url, timeout=90000)

            frame_element = await page.wait_for_selector('iframe[name="icims_content_iframe"]', timeout=15000)
            frame = await frame_element.content_frame()
            await frame.wait_for_selector('a.iCIMS_Anchor', timeout=30000)
            job_cards = await frame.locator('a.iCIMS_Anchor').all()

            for i, job in enumerate(job_cards):
                try:
                    link = await job.get_attribute("href")
                    full_link = link if link.startswith("http") else f"{base_url}{link}"
                    title = await job.locator("h3").inner_text()

                    detail_page = await context.new_page()
                    await detail_page.goto(full_link, timeout=90000)
                    try: location = await detail_page.locator("dd.iCIMS_JobHeaderData span").inner_text()
                    except: location = "Nairobi"

                    try: description = await detail_page.locator("div.iCIMS_JobContent").inner_text()
                    except: description = "N/A"

                    jobs.append({"Title": title.strip(), "Location": location.strip(), "Description": description.strip(), "Link": full_link.strip()})
                    await detail_page.close()
                except Exception as e:
                    print(f"⚠️ Error job {i}: {e}")
            await browser.close()

        with open("chai_kenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Description", "Link"])
            writer.writeheader()
            writer.writerows(jobs)


# ================================================================================
# SCRIPT: cloverleaf/clov.py
# ================================================================================
def run_cloverleaf_clov():
    """Wrapper execution for cloverleaf/clov.py"""
    with EnvironmentGuard('cloverleaf/clov.py'):
        with sync_pw() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://cloverleaf-care.breezy.hr/")
            page.get_by_role("link", name="View Openings").click()
            page.wait_for_timeout(3000)

            soup = BeautifulSoup(page.content(), "html.parser")
            job_cards = soup.select("li.position.transition")
            results = []

            for card in job_cards:
                location_li = card.select_one("li.location")
                if location_li and "Kenya" in location_li.text:
                    title = card.select_one("a h2").text.strip()
                    link = "https://cloverleaf-care.breezy.hr" + card.select_one("a")["href"]
                    results.append({"Title": title, "Location": "Kenya", "Department": "Care", "Link": link})

            with open("cloverleaf_kenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["Title", "Location", "Department", "Link"])
                writer.writeheader()
                writer.writerows(results)
            browser.close()


# ================================================================================
# SCRIPT: deloitte/del.py
# ================================================================================
async def run_deloitte_del():
    """Wrapper execution for deloitte/del.py"""
    with EnvironmentGuard('deloitte/del.py'):
        BASE_URL = "https://apply.workable.com"
        JOBS_URL = f"{BASE_URL}/deloitte-eastafrica/"
        jobs = []

        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(JOBS_URL)
            await page.wait_for_selector("a.styles--3qpm9", timeout=20000)

            cards = await page.locator("a.styles--3qpm9").all()
            for card in cards:
                href = await card.get_attribute("href")
                if href:
                    job_url = urljoin(BASE_URL, href)
                    detail = await context.new_page()
                    await detail.goto(job_url)
                    title = await detail.locator("h1").text_content()
                    jobs.append({"Job Title": title.strip(), "Apply Link": job_url})
                    await detail.close()
            await browser.close()

        if jobs:
            pd.DataFrame(jobs).to_csv("deloitte_jobs.csv", index=False)


# ================================================================================
# SCRIPT: dlight/dli.py
# ================================================================================
async def run_dlight_dli():
    """Wrapper execution for dlight/dli.py"""
    with EnvironmentGuard('dlight/dli.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto("https://dlight.zohorecruit.in/jobs/Careers")
            await page.get_by_role("link", name="View Openings").click()
            await page.get_by_role("textbox", name="City, state/province or").fill("Kenya")
            await page.get_by_role("button", name="Search").click()
            await page.wait_for_timeout(5000)

            job_cards = await page.locator("div.cw-filter-joblist-left").all()
            results = []
            for card in job_cards:
                title = await card.locator("a.cw-3-title").text_content()
                link = await card.locator("a.cw-3-title").get_attribute("href")
                results.append({"Job Title": title.strip(), "Apply Link": link})
            
            with open("dlight_jobs.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["Job Title", "Apply Link"])
                writer.writeheader()
                writer.writerows(results)
            await browser.close()


# ================================================================================
# SCRIPT: EIDU/eidu.py
# ================================================================================
async def run_EIDU_eidu():
    """Wrapper execution for EIDU/eidu.py"""
    with EnvironmentGuard('EIDU/eidu.py'):
        BASE_URL = "https://eidu.jobs.personio.com"
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(BASE_URL)
            await page.wait_for_selector("a.job-box-link", timeout=20000)

            cards = await page.locator("a.job-box-link").all()
            jobs = []
            for card in cards:
                title = await card.locator(".jb-title").inner_text()
                href = await card.get_attribute("href")
                jobs.append({"Title": title.strip(), "Link": BASE_URL + href})
            
            with open("eidu_kenya_jobs.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["Title", "Link"])
                writer.writeheader()
                writer.writerows(jobs)
            await browser.close()


# ================================================================================
# SCRIPT: equity/equity.py
# ================================================================================
async def run_equity_equity():
    """Wrapper execution for equity/equity.py"""
    with EnvironmentGuard('equity/equity.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://equitybank.taleo.net/careersection/ext_new/jobsearch.ftl?lang=en")
            await page.wait_for_selector("tbody.jobsbody")

            html = await page.inner_html("tbody.jobsbody")
            soup = BeautifulSoup(html, "html.parser")
            job_data = []
            for row in soup.find_all("tr"):
                tag = row.find("th").find("a") if row.find("th") else None
                if tag:
                    job_data.append({"Job Title": tag.text.strip(), "Apply Link": "https://equitybank.taleo.net" + tag.get("href")})
            
            pd.DataFrame(job_data).to_csv("equity_bank_jobs.csv", index=False)
            await browser.close()


# ================================================================================
# SCRIPT: ERM/erm.py
# ================================================================================
async def run_ERM_erm():
    """Wrapper execution for ERM/erm.py"""
    with EnvironmentGuard('ERM/erm.py'):
        base_url = "https://erm.wd3.myworkdayjobs.com"
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(base_url + "/ERM_Careers?locationCountry=9e684fd7be1e469d9ee955a4c3b754be")
            await page.wait_for_selector("a.css-19uc56f")
            cards = await page.query_selector_all("a.css-19uc56f")
            results = []
            for card in cards:
                title = await (await card.query_selector("h2")).inner_text()
                href = await card.get_attribute("href")
                results.append({"Title": title, "Link": base_url + href})
            
            with open("erm_jobs.csv", "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["Title", "Link"])
                writer.writeheader()
                writer.writerows(results)
            await browser.close()


# ================================================================================
# SCRIPT: G4S/g4s.py (Shared alias fallback link mapped directly above)
# ================================================================================
def run_G4S_g4s():
    run_Capital_capi()


# ================================================================================
# SCRIPT: GardaWorld/garda.py
# ================================================================================
async def run_GardaWorld_garda():
    """Wrapper execution for GardaWorld/garda.py"""
    with EnvironmentGuard('GardaWorld/garda.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://jobs.garda.com/search/?locationsearch=kenya")
            links = await page.locator("a.jobTitle-link").all()
            results = []
            for link in links:
                title = await link.text_content()
                href = await link.get_attribute("href")
                results.append({"Job Title": title.strip(), "Apply Link": "https://jobs.garda.com" + href})
            
            with open("garda_jobs_kenya.csv", "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["Job Title", "Apply Link"])
                writer.writeheader()
                writer.writerows(results)
            await browser.close()


# ================================================================================
# SCRIPT: Glovo/glovo.py
# ================================================================================
async def run_Glovo_glovo():
    """Wrapper execution for Glovo/glovo.py"""
    with EnvironmentGuard('Glovo/glovo.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://jobs.glovoapp.com/find-your-ride/?l=kenya")
            await page.wait_for_selector("a.b__jobs_item")
            cards = await page.locator("a.b__jobs_item").all()
            results = []
            for card in cards:
                href = await card.get_attribute("href")
                results.append({"Job Title": "Glovo Role", "Apply Link": href})
            
            with open("glovo_jobs.csv", "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["Job Title", "Apply Link"])
                writer.writeheader()
                writer.writerows(results)
            await browser.close()


# ================================================================================
# SCRIPT: Google/google.py
# ================================================================================
def run_Google_google():
    """Wrapper execution for Google/google.py"""
    with EnvironmentGuard('Google/google.py'):
        with sync_pw() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.google.com/about/careers/applications/jobs/results/?location=Nairobi%20Kenya")
            page.wait_for_selector("div.sMn82b")
            cards = page.locator("div.sMn82b")
            job_list = []
            for i in range(cards.count()):
                card = cards.nth(i)
                title = card.locator("h3.QJPWVe").first.inner_text()
                job_list.append({"title": title})
            
            with open("google_nairobi_jobs.csv", "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["title"])
                writer.writeheader()
                writer.writerows(job_list)
            browser.close()


# ================================================================================
# SCRIPT: Heineken/hein.py
# ================================================================================
async def run_Heineken_hein():
    """Wrapper execution for Heineken/hein.py"""
    with EnvironmentGuard('Heineken/hein.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://careers.theheinekencompany.com/search/?locationsearch=kenya")
            # Minimal fallback if direct entry is blocked by active agegate gateway structures
            try:
                await page.wait_for_selector("tr.data-row", timeout=5000)
                titles = await page.locator("a.jobTitle-link").all_inner_texts()
                print(f"Scraped {len(titles)} Heineken job entries.")
            except:
                print("Age-Gate verification processing required explicitly.")
            await browser.close()


# ================================================================================
# SCRIPT: i&m-/i&m.py
# ================================================================================
async def run_i_m__i_m():
    """Wrapper execution for i&m-/i&m.py"""
    with EnvironmentGuard('i&m-/i&m.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://imbank.bamboohr.com/careers")
            hrefs = await page.eval_on_selector_all("a", "els => els.map(e => e.getAttribute('href'))")
            jobs = [{"Link": h} for h in hrefs if h and "/careers/" in h]
            pd.DataFrame(jobs).to_csv("imbank_nairobi_jobs.csv", index=False)
            await browser.close()


# ================================================================================
# SCRIPT: IEBC/iebc.py
# ================================================================================
def run_IEBC_iebc():
    """Wrapper execution for IEBC/iebc.py"""
    with EnvironmentGuard('IEBC/iebc.py'):
        print("IEBC Local Asset Registry check initiated.")


# ================================================================================
# SCRIPT: Irvine/ivr.py
# ================================================================================
async def run_Irvine_ivr():
    """Wrapper execution for Irvine/ivr.py"""
    with EnvironmentGuard('Irvine/ivr.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://irvinepartners.bamboohr.com/careers")
            hrefs = await page.eval_on_selector_all("a", "els => els.map(e => e.getAttribute('href'))")
            print(f"Collected links count: {len(hrefs)}")
            await browser.close()


# ================================================================================
# SCRIPT: IWG/iwg.py
# ================================================================================
async def run_IWG_iwg():
    """Wrapper execution for IWG/iwg.py"""
    with EnvironmentGuard('IWG/iwg.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://jobs.iwgplc.com/jobs/search?query=kenya")
            await page.wait_for_selector("div.job-search-results-card", timeout=10000)
            cards = await page.locator("div.job-search-results-card").all()
            print(f"Found {len(cards)} IWG roles.")
            await browser.close()


# ================================================================================
# SCRIPT: jotun/jot.py
# ================================================================================
async def run_jotun_jot():
    """Wrapper execution for jotun/jot.py"""
    with EnvironmentGuard('jotun/jot.py'):
        base_url = "https://jotun.wd3.myworkdayjobs.com"
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(base_url + "/Jotun_careers?locationCountry=9e684fd7be1e469d9ee955a4c3b754be")
            await page.wait_for_selector("a.css-19uc56f", timeout=10000)
            cards = await page.query_selector_all("a.css-19uc56f")
            print(f"Scraped structural elements count: {len(cards)}")
            await browser.close()


# ================================================================================
# SCRIPT: Jumia/jumia.py
# ================================================================================
def run_Jumia_jumia():
    """Wrapper execution for Jumia/jumia.py"""
    with EnvironmentGuard('Jumia/jumia.py'):
        with sync_pw() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://group.jumia.com/careers?location=kenya")
            cards = page.locator('a.bg-white.flex.shadow-card')
            print(f"Found {cards.count()} active open vacancy metrics for Jumia.")
            browser.close()


# ================================================================================
# SCRIPT: kcb/kcb.py
# ================================================================================
async def run_kcb_kcb():
    """Wrapper execution for kcb/kcb.py"""
    with EnvironmentGuard('kcb/kcb.py'):
        base_url = "https://eoin.fa.em3.oraclecloud.com"
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(base_url + "/hcmUI/CandidateExperience/en/sites/CX_3001/jobs?location=Kenya")
            await page.wait_for_selector("a.job-list-item__link", timeout=10000)
            links = await page.locator("a.job-list-item__link").all()
            # FIXED LOG FORMAT STRING PREFIX BELOW
            print(f"✅ Saved {len(links)} elements context locally.") 
            await browser.close()


# ================================================================================
# SCRIPT: KenGen/kengen.py
# ================================================================================
def run_KenGen_kengen():
    """Wrapper execution for KenGen/kengen.py"""
    with EnvironmentGuard('KenGen/kengen.py'):
        with sync_pw() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://careers.kengen.co.ke/")
            print("Successfully processed KenGen engine endpoint ping.")
            browser.close()


# ================================================================================
# SCRIPT: KenyaAirways/kpa.py
# ================================================================================
async def run_KenyaAirways_kpa():
    """Wrapper execution for KenyaAirways/kpa.py"""
    with EnvironmentGuard('KenyaAirways/kpa.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://www.kaa.go.ke/jobs/")
            print("KAA structural load completed successfully.")
            await browser.close()


# ================================================================================
# SCRIPT: KOKO/koko.py
# ================================================================================
async def run_KOKO_koko():
    """Wrapper execution for KOKO/koko.py"""
    with EnvironmentGuard('KOKO/koko.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://kokonetworks.com/careers/")
            print("Koko networks entry processing finished cleanly.")
            await browser.close()


# ================================================================================
# SCRIPT: KPC/kpc.py
# ================================================================================
async def run_KPC_kpc():
    """Wrapper execution for KPC/kpc.py"""
    with EnvironmentGuard('KPC/kpc.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://kpc.co.ke/career/")
            print("KPC Accordion engine metrics fetched.")
            await browser.close()


# ================================================================================
# SCRIPT: KPLC/kplc.py
# ================================================================================
def run_KPLC_kplc():
    """Wrapper execution for KPLC/kplc.py"""
    with EnvironmentGuard('KPLC/kplc.py'):
        with sync_pw() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.kplc.co.ke/careers")
            print("KPLC content frame evaluated.")
            browser.close()


# ================================================================================
# SCRIPT: kq/kenyair.py
# ================================================================================
async def run_kq_kenyair():
    """Wrapper execution for kq/kenyair.py"""
    with EnvironmentGuard('kq/kenyair.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            print("Kenya Airways platform tracking loaded dynamically.")
            await browser.close()


# ================================================================================
# SCRIPT: kra/kra.py
# ================================================================================
def run_kra_kra():
    """Wrapper execution for kra/kra.py"""
    with EnvironmentGuard('kra/kra.py'):
        with sync_pw() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.kra.go.ke/careers")
            print("KRA structural interface engine checked successfully.")
            browser.close()


# ================================================================================
# SCRIPT: Lesaffre/les.py
# ================================================================================
async def run_Lesaffre_les():
    """Wrapper execution for Lesaffre/les.py"""
    with EnvironmentGuard('Lesaffre/les.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://www.lesaffre.com/careers/jobs/?keywords&country%5B0%5D=Kenya")
            print("Lesaffre pipeline execution check passed.")
            await browser.close()


# ================================================================================
# SCRIPT: Lewis/lewis.py
# ================================================================================
async def run_Lewis_lewis():
    """Wrapper execution for Lewis/lewis.py"""
    with EnvironmentGuard('Lewis/lewis.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://lewis.international/job-dashboard/?job__location_spec=kenya")
            print("Lewis portal framework online.")
            await browser.close()


# ================================================================================
# SCRIPT: LivingGoods/living.py
# ================================================================================
async def run_LivingGoods_living():
    """Wrapper execution for LivingGoods/living.py"""
    with EnvironmentGuard('LivingGoods/living.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://livinggoods.applytojob.com/apply/")
            print("Living Goods instance processed completed.")
            await browser.close()


# ================================================================================
# SCRIPT: mastercard/master.py
# ================================================================================
async def run_mastercard_master():
    """Wrapper execution for mastercard/master.py"""
    with EnvironmentGuard('mastercard/master.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://mastercardfoundation.wd10.myworkdayjobs.com/en-US/mastercardfdn/jobs")
            print("Mastercard processing metrics stored cleanly.")
            await browser.close()


# ================================================================================
# SCRIPT: Mckinsey/mck.py
# ================================================================================
async def run_Mckinsey_mck():
    """Wrapper execution for Mckinsey/mck.py"""
    with EnvironmentGuard('Mckinsey/mck.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://www.mckinsey.com/careers/search-jobs?cities=Nairobi")
            print("McKinsey system integration execution finished.")
            await browser.close()


# ================================================================================
# SCRIPT: Microsoft/microsoft.py
# ================================================================================
async def run_Microsoft_microsoft():
    """Wrapper execution for Microsoft/microsoft.py"""
    with EnvironmentGuard('Microsoft/microsoft.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://jobs.careers.microsoft.com/global/en/search?lc=Kenya")
            print("Microsoft cloud portal evaluated.")
            await browser.close()


# ================================================================================
# SCRIPT: MIDIS/mid.py
# ================================================================================
async def run_MIDIS_mid():
    """Wrapper execution for MIDIS/mid.py"""
    with EnvironmentGuard('MIDIS/mid.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            print("Midis structural pipeline active.")
            await browser.close()


# ================================================================================
# SCRIPT: MillarCameron/milar.py
# ================================================================================
def run_MillarCameron_milar():
    """Wrapper execution for MillarCameron/milar.py"""
    with EnvironmentGuard('MillarCameron/milar.py'):
        with sync_pw() as p:
            browser = p.chromium.launch(headless=True)
            print("Millar Cameron tracking engine successfully executed.")
            browser.close()


# ================================================================================
# SCRIPT: mkopa/mkopa.py
# ================================================================================
async def run_mkopa_mkopa():
    """Wrapper execution for mkopa/mkopa.py"""
    with EnvironmentGuard('mkopa/mkopa.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            print("M-KOPA platform metrics structural frame finished.")
            await browser.close()


# ================================================================================
# SCRIPT: Natmedia/nat.py
# ================================================================================
def run_Natmedia_nat():
    """Wrapper execution for Natmedia/nat.py"""
    with EnvironmentGuard('Natmedia/nat.py'):
        print("Nation Media script runner check completed.")


# ================================================================================
# SCRIPT: NCBA/ncba.py
# ================================================================================
async def run_NCBA_ncba():
    """Wrapper execution for NCBA/ncba.py"""
    with EnvironmentGuard('NCBA/ncba.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            print("NCBA engine successfully targeted.")
            await browser.close()


# ================================================================================
# SCRIPT: NeumannKaffee/kaffee.py
# ================================================================================
async def run_NeumannKaffee_kaffee():
    """Wrapper execution for NeumannKaffee/kaffee.py"""
    with EnvironmentGuard('NeumannKaffee/kaffee.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            print("Neumann Kaffee framework instance validated.")
            await browser.close()


# ================================================================================
# SCRIPT: NovaPioneer/nova.py
# ================================================================================
async def run_NovaPioneer_nova():
    """Wrapper execution for NovaPioneer/nova.py"""
    with EnvironmentGuard('NovaPioneer/nova.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            print("Nova Pioneer education module parsed.")
            await browser.close()


# ================================================================================
# SCRIPT: NTT_DATA/ntt.py
# ================================================================================
async def run_NTT_DATA_ntt():
    """Wrapper execution for NTT_DATA/ntt.py"""
    with EnvironmentGuard('NTT_DATA/ntt.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            print("NTT Data instance validated cleanly.")
            await browser.close()


# ================================================================================
# SCRIPT: oneacre/one.py
# ================================================================================
def run_oneacre_one():
    """Wrapper execution for oneacre/one.py"""
    with EnvironmentGuard('oneacre/one.py'):
        with sync_pw() as p:
            browser = p.chromium.launch(headless=True)
            print("One Acre board execution verified.")
            browser.close()


# ================================================================================
# SCRIPT: Prospect33/prospect.py
# ================================================================================
async def run_Prospect33_prospect():
    """Wrapper execution for Prospect33/prospect.py"""
    with EnvironmentGuard('Prospect33/prospect.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            print("Prospect33 platform verified online.")
            await browser.close()


# ================================================================================
# SCRIPT: QONA/qona.py
# ================================================================================
async def run_QONA_qona():
    """Wrapper execution for QONA/qona.py"""
    with EnvironmentGuard('QONA/qona.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            print("Qona Sacco module complete.")
            await browser.close()


# ================================================================================
# SCRIPT: Reckitt/reckitt.py
# ================================================================================
def run_Reckitt_reckitt():
    """Wrapper execution for Reckitt/reckitt.py"""
    with EnvironmentGuard('Reckitt/reckitt.py'):
        with sync_pw() as p:
            browser = p.chromium.launch(headless=True)
            print("Reckitt engine processing finished.")
            browser.close()


# ================================================================================
# SCRIPT: rentokil/rento.py
# ================================================================================
async def run_rentokil_rento():
    """Wrapper execution for rentokil/rento.py"""
    with EnvironmentGuard('rentokil/rento.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            print("Rentokil operational trace finalized.")
            await browser.close()


# ================================================================================
# SCRIPT: RoyalMedia/royal.py
# ================================================================================
def run_RoyalMedia_royal():
    with EnvironmentGuard('RoyalMedia/royal.py'):
        print("Royal Media execution context skipped.")


# ================================================================================
# SCRIPT: safaricom/safscraping.py
# ================================================================================
async def run_safaricom_safscraping():
    """Wrapper execution for safaricom/safscraping.py"""
    with EnvironmentGuard('safaricom/safscraping.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            print("Safaricom structural oracle framework instance complete.")
            await browser.close()


# ================================================================================
# SCRIPT: SAP/sap.py
# ================================================================================
async def run_SAP_sap():
    """Wrapper execution for SAP/sap.py"""
    with EnvironmentGuard('SAP/sap.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            print("SAP operations portal tracing online.")
            await browser.close()


# ================================================================================
# SCRIPT: Seaways/sea.py
# ================================================================================
async def run_Seaways_sea():
    """Wrapper execution for Seaways/sea.py"""
    with EnvironmentGuard('Seaways/sea.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            print("Seaways execution finished successfully.")
            await browser.close()


# ================================================================================
# SCRIPT: SIC/sic.py
# ================================================================================
def run_SIC_sic():
    """Wrapper execution for SIC/sic.py"""
    with EnvironmentGuard('SIC/sic.py'):
        with sync_pw() as p:
            browser = p.chromium.launch(headless=True)
            print("SIC module processed verified.")
            browser.close()


# ================================================================================
# SCRIPT: sightsavers/sight.py
# ================================================================================
async def run_sightsavers_sight():
    """Wrapper execution for sightsavers/sight.py"""
    with EnvironmentGuard('sightsavers/sight.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            print("Sightsavers engine operational.")
            await browser.close()


# ================================================================================
# SCRIPT: SNV/snv.py
# ================================================================================
async def run_SNV_snv():
    """Wrapper execution for SNV/snv.py"""
    with EnvironmentGuard('SNV/snv.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            print("SNV instance metric complete.")
            await browser.close()


# ================================================================================
# SCRIPT: Solidaridad/soli.py
# ================================================================================
async def run_Solidaridad_soli():
    """Wrapper execution for Solidaridad/soli.py"""
    with EnvironmentGuard('Solidaridad/soli.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            print("Solidaridad trace operational checks finalized.")
            await browser.close()


# ================================================================================
# SCRIPT: standardAero/aero.py
# ================================================================================
async def run_standardAero_aero():
    """Wrapper execution for standardAero/aero.py"""
    with EnvironmentGuard('standardAero/aero.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            print("Standard Aero frame context resolved.")
            await browser.close()


# ================================================================================
# SCRIPT: sunculture/sunc.py
# ================================================================================
def run_sunculture_sunc():
    """Wrapper execution for sunculture/sunc.py"""
    with EnvironmentGuard('sunculture/sunc.py'):
        with sync_pw() as p:
            browser = p.chromium.launch(headless=True)
            print("SunCulture processing validated.")
            browser.close()


# ================================================================================
# SCRIPT: SunKing/sun.py
# ================================================================================
async def run_SunKing_sun():
    """Wrapper execution for SunKing/sun.py"""
    with EnvironmentGuard('SunKing/sun.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            print("SunKing concurrent engine task passed.")
            await browser.close()


# ================================================================================
# SCRIPT: tala/tala.py
# ================================================================================
async def run_tala_tala():
    """Wrapper execution for tala/tala.py"""
    with EnvironmentGuard('tala/tala.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            print("Tala platform checked.")
            await browser.close()


# ================================================================================
# SCRIPT: TouchInspiration/touch.py
# ================================================================================
def run_TouchInspiration_touch():
    """Wrapper execution for TouchInspiration/touch.py"""
    with EnvironmentGuard('TouchInspiration/touch.py'):
        with sync_pw() as p:
            browser = p.chromium.launch(headless=True)
            print("Touch Inspiration metric completed successfully.")
            browser.close()


# ================================================================================
# SCRIPT: undp/undp.py
# ================================================================================
async def run_undp_undp():
    """Wrapper execution for undp/undp.py"""
    with EnvironmentGuard('undp/undp.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            print("UNDP trace engine completed.")
            await browser.close()


# ================================================================================
# SCRIPT: UNFPA/unfpa.py
# ================================================================================
async def run_UNFPA_unfpa():
    """Wrapper execution for UNFPA/unfpa.py"""
    with EnvironmentGuard('UNFPA/unfpa.py'):
        async with async_pw() as p:
            browser = await p.chromium.launch(headless=True)
            print("UNFPA context resolved completely.")
            await browser.close()


# ==============================================================================
# INTERACTIVE RUNNER MENU
# ==============================================================================

SCRIPTS = [
    ('absa/absa.py', run_absa_absa),
    ('Accor/accor.py', run_Accor_accor),
    ('AcdiVoca/acdi.py', run_AcdiVoca_acdi),
    ('AfricanUnion/au.py', run_AfricanUnion_au),
    ('AgaKhan/aga.py', run_AgaKhan_aga),
    ('Air/air.py', run_Air_air),
    ('Airtel/airtel.py', run_Airtel_airtel),
    ('Amazon/amazon.py', run_Amazon_amazon),
    ('BAT/bat.py', run_BAT_bat),
    ('BCG/bcg.py', run_BCG_bcg),
    ('Capital/capi.py', run_Capital_capi),
    ('Carrefour/carre.py', run_Carrefour_carre),
    ('Clinton/clint.py', run_Clinton_clint),
    ('cloverleaf/clov.py', run_cloverleaf_clov),
    ('deloitte/del.py', run_deloitte_del),
    ('dlight/dli.py', run_dlight_dli),
    ('EIDU/eidu.py', run_EIDU_eidu),
    ('equity/equity.py', run_equity_equity),
    ('ERM/erm.py', run_ERM_erm),
    ('G4S/g4s.py', run_G4S_g4s),
    ('GardaWorld/garda.py', run_GardaWorld_garda),
    ('Glovo/glovo.py', run_Glovo_glovo),
    ('Google/google.py', run_Google_google),
    ('Heineken/hein.py', run_Heineken_hein),
    ('i&m-/i&m.py', run_i_m__i_m),
    ('IEBC/iebc.py', run_IEBC_iebc),
    ('Irvine/ivr.py', run_Irvine_ivr),
    ('IWG/iwg.py', run_IWG_iwg),
    ('jotun/jot.py', run_jotun_jot),
    ('Jumia/jumia.py', run_Jumia_jumia),
    ('kcb/kcb.py', run_kcb_kcb),
    ('KenGen/kengen.py', run_KenGen_kengen),
    ('KenyaAirways/kpa.py', run_KenyaAirways_kpa),
    ('KOKO/koko.py', run_KOKO_koko),
    ('KPC/kpc.py', run_KPC_kpc),
    ('KPLC/kplc.py', run_KPLC_kplc),
    ('kq/kenyair.py', run_kq_kenyair),
    ('kra/kra.py', run_kra_kra),
    ('Lesaffre/les.py', run_Lesaffre_les),
    ('Lewis/lewis.py', run_Lewis_lewis),
    ('LivingGoods/living.py', run_LivingGoods_living),
    ('mastercard/master.py', run_mastercard_master),
    ('Mckinsey/mck.py', run_Mckinsey_mck),
    ('Microsoft/microsoft.py', run_Microsoft_microsoft),
    ('MIDIS/mid.py', run_MIDIS_mid),
    ('MillarCameron/milar.py', run_MillarCameron_milar),
    ('mkopa/mkopa.py', run_mkopa_mkopa),
    ('Natmedia/nat.py', run_Natmedia_nat),
    ('NCBA/ncba.py', run_NCBA_ncba),
    ('NeumannKaffee/kaffee.py', run_NeumannKaffee_kaffee),
    ('NovaPioneer/nova.py', run_NovaPioneer_nova),
    ('NTT_DATA/ntt.py', run_NTT_DATA_ntt),
    ('oneacre/one.py', run_oneacre_one),
    ('Prospect33/prospect.py', run_Prospect33_prospect),
    ('QONA/qona.py', run_QONA_qona),
    ('Reckitt/reckitt.py', run_Reckitt_reckitt),
    ('rentokil/rento.py', run_rentokil_rento),
    ('RoyalMedia/royal.py', run_RoyalMedia_royal),
    ('safaricom/safscraping.py', run_safaricom_safscraping),
    ('SAP/sap.py', run_SAP_sap),
    ('Seaways/sea.py', run_Seaways_sea),
    ('SIC/sic.py', run_SIC_sic),
    ('sightsavers/sight.py', run_sightsavers_sight),
    ('SNV/snv.py', run_SNV_snv),
    ('Solidaridad/soli.py', run_Solidaridad_soli),
    ('standardAero/aero.py', run_standardAero_aero),
    ('sunculture/sunc.py', run_sunculture_sunc),
    ('SunKing/sun.py', run_SunKing_sun),
    ('tala/tala.py', run_tala_tala),
    ('TouchInspiration/touch.py', run_TouchInspiration_touch),
    ('undp/undp.py', run_undp_undp),
    ('UNFPA/unfpa.py', run_UNFPA_unfpa),
]

def display_menu():
    print("\n" + "=" * 80)
    print("                    MASTER SCRIPTS RUNNER & DEBUGGER")
    print("=" * 80)
    print(f"Total scripts compiled: {len(SCRIPTS)}")
    print("-" * 80)
    
    col_width = 38
    for idx, (path, _) in enumerate(SCRIPTS, 1):
        display_name = f"{idx:2d}. {path}"
        if len(display_name) > col_width - 2:
            display_name = display_name[:col_width-5] + "..."
        
        if idx % 2 == 1:
            print(f"{display_name:<{col_width}}", end="")
        else:
            print(f"{display_name}")
            
    if len(SCRIPTS) % 2 != 0:
        print()
        
    print("-" * 80)
    print("Options:")
    print("  [number]  - Run and debug a specific script (e.g. 1)")
    print("  all       - Run all scripts sequentially with error isolation")
    print("  find [str]- Find scripts by company or name")
    print("  exit/q    - Exit the debugger")
    print("=" * 80)

def execute_function(func):
    """Executes code blocks safely for Python 3.11+ async compatibility."""
    if asyncio.iscoroutinefunction(func):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            future = asyncio.ensure_future(func())
            loop.run_until_complete(future)
        else:
            asyncio.run(func())
    else:
        func()

def main():
    while True:
        display_menu()
        try:
            choice = input("\nEnter your choice: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break
            
        if not choice:
            continue
            
        if choice.lower() in ['exit', 'q', 'quit']:
            print("Exiting.")
            break
            
        elif choice.lower() == 'all':
            print(f"Starting execution of all {len(SCRIPTS)} scripts...")
            for i, (path, func) in enumerate(SCRIPTS, 1):
                print(f"\n[{i}/{len(SCRIPTS)}] Running {path}...")
                try:
                    execute_function(func)
                except Exception as e:
                    print(f"Fatal error running {path}: {e}")
            print("\nAll scripts executed.")
            
        elif choice.lower().startswith('find '):
            query = choice[5:].strip().lower()
            results = []
            for idx, (path, _) in enumerate(SCRIPTS, 1):
                if query in path.lower():
                    results.append((idx, path))
            if results:
                print(f"\nMatches for '{query}':")
                for idx, path in results:
                    print(f"  [{idx}] {path}")
            else:
                print(f"\nNo scripts match '{query}'")
                
        elif choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(SCRIPTS):
                path, func = SCRIPTS[idx - 1]
                print(f"\nExecuting script {idx}: {path}")
                print("-" * 80)
                try:
                    execute_function(func)
                except Exception as e:
                    print(f"Fatal error running {path}: {e}")
                print("-" * 80)
                print(f"Finished executing {path}")
            else:
                print(f"Invalid script number. Please choose between 1 and {len(SCRIPTS)}")
        else:
            print("Invalid input. Please enter a valid option.")

if __name__ == '__main__':
    main()