from playwright.sync_api import sync_playwright

BASE_URL = "https://www.amazon.jobs"
SEARCH_URL = f"{BASE_URL}/en/search?base_query=&loc_query=Kenya&country=KEN"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f"Visiting {SEARCH_URL}...")
        page.goto(SEARCH_URL)
        page.wait_for_timeout(10000)
        page.screenshot(path="amazon_screenshot.png")
        print("Screenshot saved to amazon_screenshot.png")
        
        # Check if there are any anchor tags or buttons or specific classes
        links = page.locator("a").all()
        print(f"Total links: {len(links)}")
        
        # Look for any containing "job" or similar
        job_related = []
        for link in links:
            href = link.get_attribute("href")
            text = link.inner_text().strip()
            cls = link.get_attribute("class")
            if href and ("/jobs/" in href or "/job/" in href or "job" in href or (cls and "job" in cls)):
                job_related.append((href, text, cls))
        
        print(f"Job related links ({len(job_related)}):")
        for href, text, cls in job_related[:15]:
            print(f"  href: {href}, text: {text}, class: {cls}")
            
        # Print first 1000 chars of body text
        body_text = page.locator("body").inner_text()
        print("--- BODY TEXT ---")
        print(body_text[:1500])
        print("-----------------")
        
        browser.close()

if __name__ == "__main__":
    run()
