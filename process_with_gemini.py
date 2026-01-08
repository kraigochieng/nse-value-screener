import csv
import io
import json
import time

import httpx
from google import genai

from schemas import (
    FinancialReportExtraction,
)
from settings import settings

INPUT_CSV = "annual_reports_ready_for_ai.csv"
OUTPUT_JSONL = "financial_data_extracted.jsonl"


def main():
    client = genai.Client(api_key=settings.gemini_api_key)

    # Load rows to process
    reports = []
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        reports = list(reader)

    print(f">>> Found {len(reports)} reports to process.")

    for i, report in enumerate(reports):
        title = report.get("title", "Unknown")
        download_url = report.get("direct_download_url")

        # Skip if no URL
        if not download_url:
            print(f"[{i + 1}] Skipping {title} (No URL)")
            continue

        print(f"\n[{i + 1}/{len(reports)}] Processing: {title}")

        try:
            # 1. Download Bytes to RAM
            print("   -> Streaming PDF bytes...")
            # Follow redirects=True is CRITICAL for Google Drive links
            response = httpx.get(download_url, follow_redirects=True, timeout=120)
            response.raise_for_status()

            # 2. Upload to Gemini
            print("   -> Uploading to Gemini Files API...")
            file_stream = io.BytesIO(response.content)

            uploaded_file = client.files.upload(
                file=file_stream,
                config=dict(mime_type="application/pdf", display_name=title),
            )

            # Wait for processing
            while uploaded_file.state.name == "PROCESSING":
                print("   -> Waiting for processing...")
                time.sleep(2)
                uploaded_file = client.files.get(name=uploaded_file.name)

            if uploaded_file.state.name == "FAILED":
                print("   -> Gemini Processing FAILED.")
                continue

            # 3. Generate Content (The Extraction)
            print("   -> Extracting financial data...")
            prompt = """
            Analyze this financial report. Extract the specific values for the Income Statement, 
            Balance Sheet, and Cash Flow statement for the most recent fiscal year available.
            
            If a field is not present, return null. 
            Ensure you capture the correct scale (e.g. if 'in millions', extract the number as seen).
            """

            response = client.models.generate_content(
                model="gemini-2.0-flash",  # Use 2.0-flash or 1.5-pro for best doc analysis
                contents=[uploaded_file, prompt],
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": FinancialReportExtraction.model_json_schema(),
                },
            )

            # 4. Validate & Save
            # We parse it to ensure it matches our model
            data_obj = FinancialReportExtraction.model_validate_json(response.text)

            # Convert back to dict for saving
            result_dict = data_obj.model_dump()
            result_dict["source_title"] = title  # Add metadata

            # Append to JSONL file (safer than rewriting a huge JSON array)
            with open(OUTPUT_JSONL, "a", encoding="utf-8") as outfile:
                json.dump(result_dict, outfile)
                outfile.write("\n")

            print(f"   -> SUCCESS! Saved data for {data_obj.company_name}")

            # 5. Cleanup (Save Quota!)
            client.files.delete(name=uploaded_file.name)
            print("   -> Cleanup: File deleted.")

        except Exception as e:
            print(f"   -> ERROR: {e}")
            # Optional: Log error to a separate file


if __name__ == "__main__":
    main()
