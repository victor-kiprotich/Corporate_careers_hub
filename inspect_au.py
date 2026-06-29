import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navigating to all AU jobs...")
        await page.goto("https://jobs.au.int/search/?searchResultView=LIST&markerViewed=&carouselIndex=&facetFilters=%7B%22mfield1%22%3A%5B%22Kenya%22%5D%7D&pageNumber=0")
        await page.wait_for_timeout(10000)
        
        # Take a screenshot
        await page.screenshot(path="au_all_screenshot.png")
        print("Screenshot saved to au_all_screenshot.png")
        
        # Check text content of the page
        text = await page.inner_text("body")
        print("--- BODY TEXT ---")
        print(text[:2000])
        print("-----------------")
                
        await browser.close()

asyncio.run(run())
