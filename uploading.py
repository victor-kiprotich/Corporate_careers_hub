import os
import sys
import json
import pandas as pd
import gspread
from tqdm import tqdm
from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import SpreadsheetNotFound
# =========================
# CONFIG
# =========================
CSV_FOLDER = "JOB_FILES"
GOOGLE_SHEET_NAME = "Kazimap"
CREDENTIALS_FILE = "kazimap.json"
SKIPPED_LOG_FILE = "skipped_files.txt"
# =========================
# AUTHENTICATION
# =========================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)

with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
    service_account_email = json.load(f)["client_email"]

print(f"Using service account: {service_account_email}")
# =========================
# OPEN GOOGLE SHEET
# =========================
try:
    spreadsheet = client.open(GOOGLE_SHEET_NAME)
except SpreadsheetNotFound:
    print(
        f"❌ Spreadsheet '{GOOGLE_SHEET_NAME}' not found.\n"
        f"   Make sure it exists and is shared with:\n"
        f"   {service_account_email}"
    )
    sys.exit(1)
# =========================
# PROCESS CSV FILES
# =========================
skipped_empty = []
skipped_error = []
uploaded = []
if not os.path.isdir(CSV_FOLDER):
    sys.exit(f"❌ CSV folder not found: {CSV_FOLDER}")

csv_files = [f for f in os.listdir(CSV_FOLDER) if f.lower().endswith(".csv")]
if not csv_files:
    sys.exit("❌ No CSV files found in the JOB_FILES folder!")

for file in tqdm(csv_files, desc="Uploading CSVs"):
    website_name = os.path.splitext(file)[0]
    file_path = os.path.join(CSV_FOLDER, file)

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        msg = f"{file} | error reading: {e}"
        print(f"❌ {msg}")
        skipped_error.append(msg)
        continue

    if df.empty:
        print(f"⚠️ Skipping empty CSV: {file}")
        skipped_empty.append(file)
        continue
    # Clean data
    df.replace([float("inf"), float("-inf")], pd.NA, inplace=True)
    df.fillna("", inplace=True)
    df = df.astype(str)

    # Create or clear worksheet
    try:
        try:
            sheet = spreadsheet.worksheet(website_name)
            sheet.clear()
        except gspread.exceptions.WorksheetNotFound:
            sheet = spreadsheet.add_worksheet(title=website_name, rows="100", cols="20")

        # Upload header + rows in batches
        header = [df.columns.tolist()]
        rows = df.values.tolist()
        sheet.update("A1", header + rows)
        uploaded.append(f"{website_name}: {len(df)} jobs")

    except Exception as e:
        msg = f"{file} | error uploading: {e}"
        print(f"❌ {msg}")
        skipped_error.append(msg)

# =========================
# WRITE SKIPPED FILE LOG
# =========================
with open(SKIPPED_LOG_FILE, "w", encoding="utf-8") as f:
    f.write("Skipped CSV Report\n")
    f.write("==================\n")
    if skipped_empty:
        f.write("\nEmpty CSVs:\n")
        for name in skipped_empty:
            f.write(f"- {name}\n")
    if skipped_error:
        f.write("\nErrored CSVs:\n")
        for msg in skipped_error:
            f.write(f"- {msg}\n")
    if not skipped_empty and not skipped_error:
        f.write("\nNo skipped files. All good!\n")

print(f"\n📝 Skipped-file log written to: {os.path.abspath(SKIPPED_LOG_FILE)}")

# =========================
# SUMMARY OUTPUT
# =========================
print("\n---- Upload Summary ----")
for u in uploaded:
    print(u)
print(f"Total non-empty CSVs uploaded: {len(uploaded)}")
print("----------------------------")
