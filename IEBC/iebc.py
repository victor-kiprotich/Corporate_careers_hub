import pdfplumber

PDF_URL = "https://www.iebc.or.ke/internaljobs/Internal_jobs_May_2021.pdf"
LOCAL_PDF = "iebc_jobs.pdf"

import requests

# Download the PDF file
response = requests.get(PDF_URL)
with open(LOCAL_PDF, "wb") as f:
    f.write(response.content)

