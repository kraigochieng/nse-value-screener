import pandas as pd
from playwright.sync_api import sync_playwright

from utils import convert_to_download_url


def main():
    input_csv = "annual_reports_queue_20260108_102010_cleaned.csv"
    output_csv = "annual_reports_ready_for_ai.csv"

    # Read the existing CSV
    try:
        df = pd.read_csv(input_csv)
    except FileNotFoundError:
        print(f"Error: {input_csv} not found.")
        return

    # Create new columns if they don't exist
    if "direct_download_url" not in df.columns:
        df["direct_download_url"] = None

    print(f">>> Processing {len(df)} reports...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Use True for speed later
        page = browser.new_page()

        # Iterate through rows
        # We use iterrows for simplicity, though batch processing is faster for massive datasets
        for index, row in df.iterrows():
            # Skip if we already have a link (allows restarting script)
            if pd.notna(row["direct_download_url"]):
                continue

            title = row["title"]
            doc_url = row["document_url"]
            print(f"[{index + 1}/{len(df)}] Fetching URL for: {title}")

            try:
                page.goto(doc_url, timeout=60000)

                # Wait for the iframe to attach
                iframe_locator = page.locator("#annual-report")
                iframe_locator.wait_for(state="attached", timeout=60000)

                # Extract SRC
                raw_drive_url = iframe_locator.get_attribute("src")

                # Convert to direct link
                direct_link = convert_to_download_url(raw_drive_url)

                if direct_link:
                    print(f"    -> Found: {direct_link}")
                    df.at[index, "direct_download_url"] = direct_link

                    # Save progress every 5 rows to be safe
                    if index % 5 == 0:
                        df.to_csv(output_csv, index=False)
                else:
                    print("    -> ERROR: Could not extract ID.")

            except Exception as e:
                print(f"    -> FAILED: {e}")

        browser.close()

    # Final Save
    df.to_csv(output_csv, index=False)
    print(f">>> Done! Saved to {output_csv}")


if __name__ == "__main__":
    main()
