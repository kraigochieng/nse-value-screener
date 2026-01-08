import csv
import os
import re
import time

from playwright.sync_api import sync_playwright


def convert_to_download_url(drive_preview_url):
    """
    Input:  https://drive.google.com/file/d/1FZkJkg4DpTkGen.../preview
    Output: https://drive.google.com/uc?export=download&id=1FZkJkg4DpTkGen...
    """
    if not drive_preview_url:
        return None

    # Extract ID between /d/ and /preview (or /view)
    match = re.search(r"/d/([^/]+)", drive_preview_url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return None


def main():
    # 1. Setup paths
    input_csv = "annual_reports_queue_20260108_102010_cleaned.csv"
    output_dir = "downloaded_reports"
    os.makedirs(output_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # 2. Read the list of reports
        reports = []
        with open(input_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            reports = list(reader)

        print(f">>> Found {len(reports)} reports to process.")

        for i, report in enumerate(reports):
            title = report["title"]
            doc_url = report["document_url"]

            # Create a safe filename (remove illegal characters like / or :)
            safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
            save_path = os.path.join(output_dir, f"{safe_title}.pdf")

            print(f"\n[{i + 1}/{len(reports)}] Processing: {title}")

            if os.path.exists(save_path):
                print("   -> File already exists. Skipping.")
                continue

            try:
                # 1. Go to page
                page.goto(doc_url, timeout=60000)

                # 2. Get the iframe SRC directly (No clicking needed!)
                # We wait for the iframe to be attached to the DOM
                iframe_locator = page.locator("#annual-report")
                iframe_locator.wait_for(state="attached", timeout=10000)

                drive_preview_url = iframe_locator.get_attribute("src")
                print(f"   -> Found Drive URL: {drive_preview_url}")

                # 3. Convert to download link
                download_link = convert_to_download_url(drive_preview_url)

                if download_link:
                    print("   -> Downloading...")
                    # 4. Download directly via Python request
                    response = page.request.get(download_link, timeout=300000)

                    if response.status == 200:
                        with open(save_path, "wb") as f:
                            f.write(response.body())
                        print("   -> SUCCESS.")
                    else:
                        print(f"   -> ERROR: Status {response.status}")
                else:
                    print("   -> ERROR: Could not extract ID from iframe src.")

            except Exception as e:
                print(f"   -> FAILED: {e}")

        browser.close()


if __name__ == "__main__":
    main()
