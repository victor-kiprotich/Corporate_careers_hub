import os
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.kplc.co.ke"
CAREERS_URL = f"{BASE_URL}/careers"
DOWNLOAD_DIR = "kplc_pdfs"

def download_pdf(pdf_url, filename):
    response = requests.get(pdf_url)
    if response.status_code == 200:
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        path = os.path.join(DOWNLOAD_DIR, filename)
        with open(path, "wb") as f:
            f.write(response.content)
        print(f"✅ Downloaded: {filename}")
    else:
        print(f"❌ Failed to download {filename}")

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    print("🌐 Visiting Kenya Power Careers Page...")
    page.goto(CAREERS_URL, timeout=60000)
    page.wait_for_timeout(3000)

    html = page.content()
    soup = BeautifulSoup(html, "html.parser")

    job_section = soup.find("div", class_="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-8")
    if not job_section:
        print("❌ Could not find job section.")
        return

    links = job_section.find_all("a", href=True)
    pdf_links = [
        (link["href"], link.get_text(strip=True))
        for link in links if link["href"].lower().endswith(".pdf")
    ]

    if not pdf_links:
        print("⚠️ No PDF links found.")
    else:
        print(f"📄 Found {len(pdf_links)} PDF(s). Starting download...")

        for href, text in pdf_links:
            full_url = href if href.startswith("http") else BASE_URL + href
            filename = href.split("/")[-1]
            download_pdf(full_url, filename)

    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
