import csv
import time
from pprint import pprint

from playwright.sync_api import sync_playwright


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        print(">>> Main page")
        try:
            page.goto(
                "https://africanfinancials.com/kenya-listed-company-documents/",
                timeout=60000,
                wait_until="domcontentloaded",
            )
        except Exception as e:
            print(f"Initial navigation failed: {e}")
            return

        print(">>> Waiting for the initial list to load fully...")
        page.locator(".af20-news").first.wait_for(state="visible", timeout=30000)

        print(">>> Filtering to 'Annual Reports'")
        dropdown = page.locator('select[name="wpv-document-type"]')
        dropdown.select_option("annual-reports")

        print(">>> Waiting for filter to update the table...")
        time.sleep(2)
        page.locator(".af20-news").first.wait_for(state="visible", timeout=30000)
        first_item_text = page.locator(".af20-news").first.inner_text()
        print(
            f">>> List refreshed. First item found: {first_item_text.splitlines()[0]}"
        )

        csv_filename = "annual_reports_queue.csv"
        fieldnames = ["title", "document_url", "company_url", "page_number"]

        with open(csv_filename, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

        print(f">>> Created {csv_filename}.")

        page_num = 1

        while True:
            print(f"--- Processing Page {page_num} ---")

            try:
                page.locator(".af20-news").first.wait_for(
                    state="visible", timeout=10000
                )
            except Exception as e:
                print(
                    f">>> No visible cards found (list might be empty). Ending: {str(e)}"
                )
                break

            page.locator(".af20-news").first.wait_for()
            cards = page.locator(".af20-news").all()
            
            visible_cards = [card for card in cards if card.is_visible()]
            print(f"    Found {len(visible_cards)} visible cards.")
            
            current_page_data = []

            for card in visible_cards:
                try:
                    title = card.locator("h2 a").inner_text()
                    doc_url = card.locator("h2 a").get_attribute("href")
                    company_url = card.locator("cite a").get_attribute("href")

                    current_page_data.append(
                        {
                            "title": title,
                            "document_url": doc_url,
                            "company_url": company_url,
                            "page_number": page_num,
                        }
                    )
                except Exception as e:
                    print(f"Skipped a card due to error: {e}")

            if current_page_data:
                with open(csv_filename, mode="a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerows(current_page_data)
                print(f"    Saved {len(current_page_data)} reports to CSV.")

            next_button = page.locator(".wpv-archive-pagination-links-next-link")

            if next_button.is_visible():
                next_page_num = page_num + 1

                next_button.click()

                try:
                    page.wait_for_selector(
                        f'.wpv-archive-pagination-link-current:has-text("{next_page_num}")',
                        timeout=30000,
                    )
                    page_num += 1
                    time.sleep(2)
                except Exception:
                    print(">>> Pagination timed out or finished.")
                    break
            else:
                print(">>> No 'Next' button found. Reached end of list.")
                break

        print(">>> Harvest complete!")
        browser.close()


if __name__ == "__main__":
    main()
