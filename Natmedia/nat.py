import requests
from bs4 import BeautifulSoup
import csv

# Base URL and parameters
BASE_URL = "https://career.staffingsoft.com/jobsAjax"
PARAMS = {
    "clientid": "NMG",
    "Country": "KE"  # KE = Kenya
}
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_kenya_jobs():
    response = requests.get(BASE_URL, params=PARAMS, headers=HEADERS)
    response.raise_for_status()  # Will raise error if response isn't 200

    soup = BeautifulSoup(response.text, "html.parser")
    job_cards = soup.select(".jobDiv")

    print(f"🔎 Found {len(job_cards)} Kenya-based jobs")

    jobs = []

    for card in job_cards:
        try:
            title_tag = card.select_one("a")
            title = title_tag.text.strip() if title_tag else "N/A"
            link = "https://career.staffingsoft.com" + title_tag['href'] if title_tag else "N/A"

            location = card.select_one(".jobLocation")
            location_text = location.text.strip() if location else "N/A"

            posting_date = card.select_one(".jobPostDate")
            post_date_text = posting_date.text.strip() if posting_date else "N/A"

            jobs.append({
                "Job Title": title,
                "Location": location_text,
                "Posting Date": post_date_text,
                "Apply Link": link
            })
        except Exception as e:
            print(f"⚠️ Skipping job due to error: {e}")

    return jobs

def save_to_csv(jobs, filename="nmg_kenya_jobs.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Job Title", "Location", "Posting Date", "Apply Link"])
        writer.writeheader()
        writer.writerows(jobs)

    print(f"\n✅ Saved {len(jobs)} jobs to {filename}")

if __name__ == "__main__":
    jobs = fetch_kenya_jobs()
    if jobs:
        save_to_csv(jobs)
    else:
        print("⚠️ No jobs found.")
